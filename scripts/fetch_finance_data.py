#!/usr/bin/env python3
"""
金融保险数据采集脚本
从公开数据源采集金融保险相关资讯
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import sys

class FinanceDataFetcher:
    """金融保险数据采集器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        })
        
        # 金融保险数据源配置
        self.data_sources = {
            'regulatory': [
                'http://www.cbirc.gov.cn/cn/view/pages/ItemList.html?itemPId=923&itemId=4114&itemUrl=ItemListRightList.html&itemName=法规文件',  # 银保监会法规
                'http://www.sse.com.cn/lawandrules/sserules/overview/',  # 上交所规则
                'http://www.szse.cn/lawrules/rule/overview/index.html',  # 深交所规则
            ],
            'news': [
                'https://www.caixin.com/search/advance?keyword=保险&sortType=time',  # 财新保险
                'https://www.yicai.com/search?keys=金融',  # 第一财经金融
                'https://www.21jingji.com/channel/finance/',  # 21财经
            ],
            'companies': [
                'http://www.insurance.gov.cn/',  # 保险行业协会
                'https://www.pingan.com/news/',  # 平安新闻
                'https://www.cpic.com.cn/news/',  # 太平洋保险新闻
            ]
        }
    
    def fetch_cbirc_regulations(self, days: int = 7) -> List[Dict]:
        """采集银保监会最新法规（模拟）"""
        # 实际应用中需要解析网页或API
        # 这里返回模拟数据
        regulations = []
        for i in range(5):
            regulations.append({
                'title': f'银保监会发布《关于规范{i+1}的通知》',
                'summary': f'为进一步规范市场秩序，银保监会发布第{i+1}号监管通知，明确相关要求。',
                'url': f'http://www.cbirc.gov.cn/cn/view/pages/ItemDetail.html?docId={1000+i}&itemId=4114',
                'source': '银保监会官网',
                'published_at': (datetime.now() - timedelta(days=i)).isoformat() + 'Z',
                'category': 'regulatory'
            })
        return regulations
    
    def fetch_insurance_news(self, days: int = 7) -> List[Dict]:
        """采集保险行业新闻（模拟）"""
        news = []
        topics = ['健康险', '车险', '寿险', '财险', '再保险']
        for i, topic in enumerate(topics):
            news.append({
                'title': f'{topic}市场迎来新机遇，多家公司推出创新产品',
                'summary': f'随着政策支持和技术发展，{topic}领域出现新的增长点，多家保险公司积极布局。',
                'url': f'https://www.caixin.com/news/{1000+i}',
                'source': '财新网',
                'published_at': (datetime.now() - timedelta(days=i)).isoformat() + 'Z',
                'category': 'industry'
            })
        return news
    
    def fetch_financial_research(self, days: int = 7) -> List[Dict]:
        """采集金融研究报告（模拟）"""
        research = []
        institutions = ['中金公司', '中信证券', '华泰证券', '国泰君安', '招商证券']
        for i, inst in enumerate(institutions):
            research.append({
                'title': f'{inst}发布《2026年保险行业投资策略报告》',
                'summary': f'{inst}最新研究报告指出，保险行业数字化转型加速，关注科技赋能带来的投资机会。',
                'url': f'https://research.{inst.lower()}.com/report/{2000+i}',
                'source': inst,
                'published_at': (datetime.now() - timedelta(days=i)).isoformat() + 'Z',
                'category': 'research'
            })
        return research
    
    def fetch_all_data(self, days: int = 7) -> List[Dict]:
        """采集所有类型数据"""
        all_data = []
        
        # 采集监管政策
        regulations = self.fetch_cbirc_regulations(days)
        all_data.extend(regulations)
        
        # 采集行业新闻
        news = self.fetch_insurance_news(days)
        all_data.extend(news)
        
        # 采集研究报告
        research = self.fetch_financial_research(days)
        all_data.extend(research)
        
        # 按发布时间排序
        all_data.sort(key=lambda x: x['published_at'], reverse=True)
        
        return all_data
    
    def save_to_json(self, data: List[Dict], output_path: str):
        """保存数据到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'count': len(data),
                'items': data,
                'generated_at': datetime.now().isoformat() + 'Z'
            }, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {output_path}")
        print(f"共采集 {len(data)} 条记录")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python fetch_finance_data.py <output_dir> [days]")
        sys.exit(1)
    
    output_dir = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建采集器并获取数据
    fetcher = FinanceDataFetcher()
    data = fetcher.fetch_all_data(days)
    
    # 生成输出文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'finance_data_{timestamp}.json')
    
    # 保存数据
    fetcher.save_to_json(data, output_file)
    
    # 同时生成一个最新的数据文件
    latest_file = os.path.join(output_dir, 'latest_finance_data.json')
    fetcher.save_to_json(data, latest_file)

if __name__ == '__main__':
    main()