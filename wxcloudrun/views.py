from datetime import datetime
from flask import render_template, request, send_file, current_app
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import os
import PyPDF2
import docx2pdf
import logging
# import urllib.request
import urllib.parse
import json
import requests


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route("/api/pdftoword", methods=["POST"])
def pdf_to_word():
    # 获取文件名、文件路径

    # 将pdf转换为word  保存在相同路径下
    # file = request.files['file']
    params = request.get_json()
    # 检查filePath参数
    if 'fileID' not in params:
        return make_err_response('缺少fileID参数')
    current_app.logger.info(params)
    fileID = params['fileID']
    download_url = get_download_url(fileID)
    # file.save(filename)

    # Convert PDF to Word
    with open(download_url, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        new_filename = os.path.splitext(download_url)[0] + '.docx'
        docx2pdf.convert(text, new_filename)

    # 文件上传   获取fileid并返回
    return get_fileid(new_filename)


def get_download_url(fileid):
    # 获取文件临时下载路径
    url = f'http://api.weixin.qq.com/tcb/batchdownloadfile'
    head = {'Content-Type': 'application/json'}
    data = {
        "env": "prod-6gifok82d52efeb7",
        "file_list": [
            {'fileid': fileid, 'max_age': 86400}
        ]
    }
    data = json.dumps(data, ensure_ascii=False)
    current_app.logger.info('data:%s' % data)
    # data = urllib.parse.urlencode(data).encode('utf-8')
    response = requests.post(url=url, headers=head, data=data)
    # current_app.logger.info('result:%s' % result)
    # response = urllib.request.urlopen(result)
    current_app.logger.info('response:%s' % response.text.encode('utf-8').decode('unicode_escape'))
    # download_url = response.read()['file_list'][0]['download_url']
    download_url = eval(response.text.encode('utf-8').decode('unicode_escape')).get('file_list')[0].get('download_url')
    current_app.logger.info('download_url:%s' % download_url)
    return download_url

def get_fileid(filename):
    # 获取文件临时下载路径
    url = f'http://api.weixin.qq.com/tcb/uploadfile'
    head = {'Content-Type': 'application/json'}
    data = {
        "env": "prod-6gifok82d52efeb7",
        "path": filename
    }
    data = json.dumps(data, ensure_ascii=False)

    response = requests.post(url=url, headers=head, data=data)
    # current_app.logger.info('response:%s' % response)
    fileid = eval(response.text.encode('utf-8').decode('unicode_escape')).get('file_id')
    current_app.logger.info('fileid:%s' % fileid)
    return fileid
