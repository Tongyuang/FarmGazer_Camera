from openai import OpenAI
import requests
import json
import os

default_messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "You are a experience farm fieldworker walk through the farm, leave a short comment of the image(the field) to your manager, don't leave advice or assumption."},
            {"type": "text", "text": "start with: Hi Boss, As I monitored today, End with: From FarmGazer."},
            {"type": "image_url",
             "image_url": 
                {"url": "https://farmgazerstorage.blob.core.windows.net/images/Kevinfarm_Plant01_2024-02-22_0.jpg?sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-03-16T08:07:06Z&st=2024-02-09T02:07:06Z&spr=https&sig=flmsaOix%2Biud3OTwOB20SI4MMx3bCRV0BDOpCgwcJls%3D",},
            },
        ],
    }
]

def post_comment(image_id, user_name, comment_text):
    url = "https://farmgazer.azurewebsites.net/api/comment"
    headers = {"Content-Type": "application/json"}
    data = {
        "imageId": image_id,
        "userName": user_name,
        "commentText": comment_text
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code in [200,201,202]:
        print("Comment posted successfully.")
    else:
        print("Failed to post comment. Status code:", response.status_code)
        print("Response:", response.text)

def get_desc_by_img_url(url_in,model="gpt-4-vision-preview",max_tokens=300):
    
    # user_name = "FarmGazer"
    # comment_text = "Your comment text here"
    
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>"))
    messages = default_messages
    messages[0]["content"][-1]["image_url"]["url"] = url_in
    try:
        response = client.chat.completions.create(
            model = model,
            messages = messages,
            max_tokens=300,
        )
        comment_text=response.choices[0].message.content
        return comment_text
    except Exception as e:
        print(e)
        return None

if __name__ == "__main__":
    url_in = "https://farmgazerstorage.blob.core.windows.net/images/Kevinfarm_Plant01_2024-02-22_1.jpg?sv=2022-11-02&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2024-03-16T08:07:06Z&st=2024-02-09T02:07:06Z&spr=https&sig=flmsaOix%2Biud3OTwOB20SI4MMx3bCRV0BDOpCgwcJls%3D"
    
    comment_text = get_desc_by_img_url(url_in)
    