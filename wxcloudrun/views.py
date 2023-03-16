from datetime import datetime
from flask import render_template, request, send_file
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import os
import PyPDF2
import docx2pdf
import logging

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

    #将pdf转换为word  保存在相同路径下
    # file = request.files['file']
    params = request.get_json()
    # 检查filePath参数
    if 'filePath' not in params:
        return make_err_response(params, '缺少filePath参数')
    logging.info(params)
    filename = params['filePath']
    # file.save(filename)

    # Convert PDF to Word
    with open(filename, 'rb') as pdf_file:
        pdf_reader = PyPDF2.PdfFileReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        new_filename = os.path.splitext(filename)[0] + '.docx'
        docx2pdf.convert(text, new_filename)

    return send_file(new_filename, as_attachment=True)
