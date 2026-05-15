import openai
import os

class DomainClassifier:
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key
        os.environ["http_proxy"] = "http://localhost:7890"
        os.environ["https_proxy"] = "http://localhost:7890"

    def openai_sdk_chat_http_api(self, messages, model="gpt-4o-mini"):
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API request error: {e}")
            return None

    def classify(self, readme_text, prediction_dict):
        """
        传入readme文本、预测结果字典，返回Result:后面的分类字符串
        """
        predictions = []
        for i in range(1, 13):
            class_key = f"Top{i} Class"
            prob_key = f"Top{i} Probability"
            if class_key in prediction_dict and prob_key in prediction_dict:
                predictions.append(f"Top{i}: {prediction_dict[class_key]} ({prediction_dict[prob_key]})")
        predictions_str = ", ".join(predictions)

        system_prompt = (
            "You are a open source project's development domain classifier. "
            "Your task is to classify the domain of a software development project according "
            "to the following text of the project description and README files. Categories include: "
            "desktop applications; ai and machine learning applications; WeChat application development; "
            "enterprise applications; web applications; mobile applications; code development tools or plugins; "
            "Server application; Game development; application Plugins; Others; 未分类 ."
            "The current model predictions for this project are as follows - " + predictions_str + ". "
            "We believe there may be issues with the labeling. Please relabel this project according to its actual "
            "application scope. Please provide the Result: and Reasons: " + readme_text
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": ""}
        ]

        response = self.openai_sdk_chat_http_api(messages, model="gpt-4o-mini")
        return self.extract_result_line(response)

    @staticmethod
    def extract_result_line(response):
        """
        提取首个出现的 "Result:" 后面的内容（去除前后空格）
        """
        if not response:
            return ""
        for line in response.splitlines():
            if line.strip().lower().startswith("result:"):
                return line.split(":", 1)[1].strip()
        return ""
