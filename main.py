import os
from loguru import logger
from apis.pc_apis import XHS_Apis
from xhs_utils.common_utils import init
from xhs_utils.data_util import handle_note_info, download_note, save_to_xlsx

class Data_Spider():
    def __init__(self):
        self.xhs_apis = XHS_Apis()
        # 用于记录上次处理的最后一个粉丝ID
        self.last_processed_id = None
        # 存储已处理ID的日志文件路径
        self.processed_log = "processed_fans.log"

    def _load_last_processed_id(self):
        """从日志文件加载上次处理的最后一个ID"""
        if os.path.exists(self.processed_log):
            with open(self.processed_log, 'r') as f:
                return f.read().strip()
        return None

    def _save_last_processed_id(self, fan_id):
        """保存最后处理的ID到日志文件"""
        with open(self.processed_log, 'w') as f:
            f.write(str(fan_id))

    def follow(self, cookies_str: str, proxies=None):
        """获取所有新增粉丝，并返回需要处理的新增粉丝列表"""
        try:
            # 加载上次处理的最后一个ID
            self.last_processed_id = self._load_last_processed_id()
            
            success, msg, connections_list = self.xhs_apis.get_all_new_connections(cookies_str)
            if not success:
                raise Exception(msg)
                
            # 筛选出未处理过的新粉丝
            new_fans = []
            for fan in connections_list:
                if self.last_processed_id and fan['id'] == self.last_processed_id:
                    break
                new_fans.append(fan)
            
            # 如果有新粉丝，更新最后处理的ID
            if new_fans:
                self.last_processed_id = new_fans[0]['id']
                self._save_last_processed_id(self.last_processed_id)
            
            logger.info(f'获取到 {len(new_fans)} 个新增粉丝')
            return new_fans, True, "成功获取新增粉丝"
            
        except Exception as e:
            logger.error(f'获取新增粉丝失败: {str(e)}')
            return [], False, str(e)
        
    def follow_user(self, target_user_id: str, cookies_str: str, proxies=None):
        """关注指定用户"""
        try:
            success, msg, res_json = self.xhs_apis.follow_user(target_user_id, cookies_str)
            logger.info(f'关注用户 {target_user_id}: {success}, msg: {msg}')
            return res_json, success, msg
        except Exception as e:
            logger.error(f'关注用户 {target_user_id} 失败: {str(e)}')
            return None, False, str(e)
    
    def auto_follow_new_fans(self, cookies_str: str, proxies=None):
        """自动关注所有新增粉丝"""
        new_fans, success, msg = self.follow(cookies_str, proxies)
        if not success:
            return False, msg
        
        results = []
        for fan in new_fans:
            user_id = fan['user']['userid']
            res_json, success, msg = self.follow_user(user_id, cookies_str, proxies)
            results.append({
                'user_id': user_id,
                'nickname': fan['user']['nickname'],
                'success': success,
                'message': msg
            })
        
        # 记录处理结果
        logger.info(f"共处理 {len(results)} 个新粉丝")
        for result in results:
            status = "成功" if result['success'] else "失败"
            logger.info(f"{status}关注用户: {result['nickname']}({result['user_id']}) - {result['message']}")
        
        return True, "自动关注完成"

if __name__ == '__main__':
    cookies_str, base_path = init()
    data_spider = Data_Spider()
    
    # 自动关注所有新增粉丝
    data_spider.auto_follow_new_fans(cookies_str)
