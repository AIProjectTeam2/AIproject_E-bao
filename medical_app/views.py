# -*- coding: utf-8 -*-
import re
import jieba
import joblib
import random
import feedparser
import numpy as np
import pandas as pd
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from .models import  UserInteraction
from sklearn.svm import SVC
from gensim.models import Word2Vec, word2vec

line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)

# 載入訓練好的模型
word2vec_model = word2vec.Word2Vec.load('word2vec.zh.300.model/word2vec.zh.300.model')
svm_model = joblib.load('svm_model.pkl')
sub0_model = joblib.load('sub0_svm_model.pkl')
sub1_model = joblib.load('sub1_svm_model.pkl')

# 載入繁體中文字典&自定義字典
jieba.set_dictionary('dict.txt')
jieba.load_userdict('userdict-corpus-v2.txt')

# 載入停用詞
with open('stopwords-zh-v2.txt', 'r', encoding='utf-8') as f:
    stop_words = [line.strip() for line in f]

# 定義大項目科別
departments = ['內科', '外科', '泌尿科', '婦產科', '耳鼻喉科', '眼科', '牙科']

# 定義常用症狀
symptoms = {
    '內科': ['頭痛', '發燒', '呼吸困難', '呼吸不順', '心悸', '氣喘', '便秘', '噁心', '嘔吐', '失眠', '胸痛', '胸悶'],
    '外科': ['外傷', '吞嚥困難', '乳房疼痛', '坐骨神經痛', '脊椎側彎', '癲癇'],
    '泌尿科': ['頻尿', '解尿疼痛', '排尿困難', '單側腰痛', '血尿', '夜尿'],
    '婦產科': ['月經不規則', '尿失禁', '經痛', '頻尿', '性傳染病'],
    '耳鼻喉科': ['耳鳴', '鼻塞', '流鼻血', '吞嚥困難', '咳嗽', '發燒'],
    '眼科': ['視力模糊', '眼睛紅腫', '乾眼症', '急性視力喪失', '眼睛痛'],
    '牙科': ['牙齒疼痛', '牙齦出血', '蛀牙', '牙齦腫大', '牙齦化膿', '口臭'],
}

# 定義細項目科別
sub_departments = {
    '內科': ['一般內科', '神經科', '胸腔科', '精神科', '心臟科', '肝膽腸胃科', '內分泌科'],
    '外科': ['一般外科', '骨科', '乳房外科', '皮膚科', '神經外科'],
}

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        signature = request.META['HTTP_X_LINE_SIGNATURE']
        body = request.body.decode('utf-8')

        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            return HttpResponse(status=403)

        return HttpResponse(status=200)
    else:
        return HttpResponse(status=405)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text
    user_interaction, created = UserInteraction.objects.get_or_create(user_id=user_id)
        
    if user_input == "@附近醫療機構":
        google_maps_url = "https://www.google.com/maps/search/?api=1&query=hospitals&query"
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=f"請點擊以下連結來查看附近的醫療機構：\n{google_maps_url}")
        )
    elif user_input == "@衛生署公告":
        feed_url = "https://www.mohw.gov.tw/rss-16-1.html"
        feed = feedparser.parse(feed_url)
        announcements = []
        for entry in feed.entries[:5]:  # 只取前5則公告
            title = entry.title
            link = entry.link
            announcements.append(f"{title}\n{link}")
        announcement_text = "\n\n".join(announcements)
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text=announcement_text)
        )
    elif user_input == "@請輸入症狀":
        user_interaction.user_status = 1
        user_interaction.save()
        line_bot_api.reply_message(
            event.reply_token, 
            TextSendMessage(text="請輸入您的症狀，我會幫助您進行初步分類。")
        )
    else:    
        user_status = user_interaction.user_status
        keywords = vectorize_input(user_input)
        if created or user_status == None:
            user_interaction.user_status = 1
            user_interaction.save()
        if keywords is not None and user_status == 1:
            response = handle_first_clustering(user_input, user_interaction) # 第一次輸入
        elif user_status == 2:
            match = re.search(r'\d+', user_input)
            if match:
                user_choice = match.group()
                if user_choice in ['1','2','3','4']:
                    response = handle_second_clustering(user_choice, user_interaction) # 第二次輸入
                else:
                    response = '請輸入編號選擇症狀，若回傳皆無相符症狀輸入 4 即可。'  
            else:
                response = '請輸入編號選擇症狀，若回傳皆無相符症狀輸入 4 即可。'            
        else:
            response = '您輸入的症狀描述不夠明確，請重新輸入！'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response))

def index(request):
    return render(request, 'index.html')

def handle_first_clustering(user_input, user_interaction):
    """ 處理第一次分群 """
    vectorized_input = vectorize_input(user_input)
    (first_cluster_label, second_cluster_label), confidence_first = cluster_input(vectorized_input)

    first_cluster_result = departments[first_cluster_label]
    second_cluster_result = departments[second_cluster_label]
    
    # 保存分群結果到 database
    user_interaction.first_cluster_label = first_cluster_label
    user_interaction.second_cluster_label = second_cluster_label
    user_interaction.user_input = user_input
    user_interaction.save()
    
    if confidence_first >= 0.8 and first_cluster_result in sub_departments:
        user_interaction.user_status = 1
        user_interaction.save()
        return refine_clustering(vectorized_input, first_cluster_result)
    elif confidence_first >= 0.8:
        user_interaction.user_status = 1
        user_interaction.save()
        return f'根據以上綜合的症狀，建議您優先至 {first_cluster_result} 就診，讓醫師進行更詳細的檢查與評估。'
    else:
        first_symptom = random.choice(symptoms[first_cluster_result])
        second_symptoms = random.sample(symptoms[second_cluster_result], 2)
        
        # 保存症狀到 database
        user_interaction.user_status = 2
        user_interaction.first_symptom = first_symptom
        user_interaction.second_symptom_1 = second_symptoms[0]
        user_interaction.second_symptom_2 = second_symptoms[1]
        user_interaction.save()
        
        return f'請問是否有以下症狀：1.{first_symptom}, 2.{second_symptoms[0]}, 3.{second_symptoms[1]}, 4.以上皆非'

def handle_second_clustering(user_choice, user_interaction):
    """ 處理使用者的第二次輸入以調整分類結果 """
    user_interaction.user_status = 1
    user_interaction.save()
    first_cluster_label = user_interaction.first_cluster_label
    second_cluster_label = user_interaction.second_cluster_label
    user_input = user_interaction.user_input
    first_symptom = user_interaction.first_symptom
    second_symptoms_1 = user_interaction.second_symptom_1
    second_symptoms_2 = user_interaction.second_symptom_2
    
    if user_choice == '1':
        if departments[first_cluster_label] in sub_departments:
            return refine_clustering(vectorize_input(user_input + first_symptom), departments[first_cluster_label])
        else:
            return f'根據以上綜合的症狀，建議您優先至 {departments[first_cluster_label]} 就診，讓醫師進行更詳細的檢查與評估。'

    elif user_choice in ['2', '3']:
        if user_choice == '2':
            vectorized_input = vectorize_input(user_input + second_symptoms_1)
        elif user_choice == '3':
            vectorized_input = vectorize_input(user_input + second_symptoms_2)
        second_cluster_label = svm_model.predict(vectorized_input)

        if departments[second_cluster_label[0]] in sub_departments:
            return refine_clustering(vectorized_input, departments[second_cluster_label[0]])
        else:
            return f'根據以上綜合的症狀，建議您優先至 {departments[second_cluster_label[0]]} 就診，讓醫師進行更詳細的檢查與評估。'

    elif user_choice == '4':
        vectorized_input = vectorize_input(user_input)
        second_cluster_label = svm_model.predict(vectorized_input)

        if departments[second_cluster_label[0]] in sub_departments:
            return refine_clustering(vectorized_input, departments[second_cluster_label[0]])
        else:
            return f'根據以上綜合的症狀，建議您優先至 {departments[second_cluster_label[0]]} 就診，讓醫師進行更詳細的檢查與評估。'   

def refine_clustering(vectorized_input, main_department):
    """ 如有需要，進行細科別分群 """
    if main_department == '內科':
        sub_cluster_label = sub0_model.predict(vectorized_input)
    elif main_department == '外科':
        sub_cluster_label = sub1_model.predict(vectorized_input)
    return f'根據以上綜合的症狀，建議您優先至 {sub_departments[main_department][sub_cluster_label[0]]} 就診，讓醫師進行更詳細的檢查與評估。'

def vectorize_input(user_input):
    """ 使用訓練好的 Word2Vec 模型對使用者的輸入進行向量化 """
    
    # 使用jieba分詞, 去停詞, 與確認詞是否存在模型中
    words = jieba.lcut(user_input)  # 使用 lcut 返回列表，而不是生成器
    words = [word for word in words if word not in stop_words and word in word2vec_model.wv]

    if not words:
        # 如果沒有詞語在模型中，返回 None 來表示這是一個無效的句子
        return None
    
    # 使用向量化模型將詞向量化後再使用平均池化轉換為分群模型使用的維度型態
    word_vectors = np.array([word2vec_model.wv[word] for word in words])
    
    if word_vectors.size == 0:
        return None
    
    sentence_vector = np.mean(word_vectors, axis=0)
    sentence_vector_2d = sentence_vector.reshape(1, -1)
    
    return sentence_vector_2d

def cluster_input(vectorized_input):
    """ 使用訓練好的 SVM 模型對使用者的輸入進行分類 """

    # 使用 SVM 模型進行預測，獲取每個類別的預測概率
    probabilities = svm_model.predict_proba(vectorized_input)
    
    # 找到預測概率最高的前兩個類別
    # probabilities 是一個 2D 陣列，每一行是每個樣本的類別概率
    prob = probabilities[0]
    top_two_indices = np.argsort(prob)[::-1][:2]
    
    # 獲取前兩個類別及其第一名概率
    top_class_1 = top_two_indices[0]
    top_class_2 = top_two_indices[1]
    prob_class_1 = prob[top_class_1]
    
    # 計算信心值（可以根據需求選擇計算方式）
    # 這裡使用預測概率作為信心值
    confidence_first = prob_class_1

    # 返回最接近的兩個類別及其對應的信心值
    return (top_class_1, top_class_2), confidence_first

