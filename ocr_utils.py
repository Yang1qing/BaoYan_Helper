from aip import AipOcr

# 配置百度云API信息
APP_ID = '120093394'
API_KEY = 'dJI9Hav9pKuLZfl1pDrCFX36'
SECRET_KEY = 'KYhRuiRzmBC3MkDVJkYkgNc9uoMsulVw'

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)


def get_text_from_image(image_path):
    """从图片中识别文本"""
    with open(image_path, 'rb') as f:
        image = f.read()

    # 调用通用文字识别接口
    result = client.basicGeneral(image)

    # 提取识别到的文本
    if 'words_result' in result:
        text = '\n'.join([item['words'] for item in result['words_result']])
        return text
    return ""


def extract_award_level(text):
    """从文本中提取奖项级别"""
    # 简单的关键词匹配，可根据实际需求优化
    levels = ['国家级', '省级', '市级', '校级', '院级']
    for level in levels:
        if level in text:
            return level
    return '未明确'