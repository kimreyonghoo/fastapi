from ultralytics import YOLO
import cv2
import os
import json

# Label List (ENG)
LABELS_ENG = [
    "Galbi-gui", "Galchi-gui", "Godeungeo-gui", "Gopchang-gui", "Dakgalbi", "Deodeok-gui", "Tteokgalbi", "Bulgogi", "Samgyeopsal", "Jangeo-gui",
    "Joge-gui", "Jogi-gui", "Hwangtae-gui", "Hoonjeo-ori", "Gyeran-guk", "Tteokguk_Mandu-guk", "Mu-guk", "Miyeok-guk", "Bugeo-guk", "Siraegi-guk",
    "Yukgaejang", "Kongnamul-guk", "Gwamegi", "Yangnyeom-chicken", "Jeotgal", "Kongjaban", "Pyeonyuk", "Pizza", "Fried-chicken", "Gat-kimchi",
    "Kkakdugi", "Nabak-kimchi", "Musengchae", "Baechu-kimchi", "Baek-kimchi", "Buchu-kimchi", "Yeolmu-kimchi", "Oi-sobagi", "Chonggak-kimchi", "Pa-kimchi",
    "Gaji-bokkeum", "Gosari-namul", "Miyeokjulgi-bokkeum", "Sokju-namul", "Sigeumchi-namul", "Aehobak-bokkeum", "Gyeongdan", "Kkul-tteok", "Songpyeon", "Mandu",
    "Ramyeon", "Mak-guksu", "Mul-naengmyeon", "Bibim-naengmyeon", "Sujebi", "Yeolmu-guksu", "Janchi-guksu", "Jjajangmyeon", "Jjamppong", "Jjolmyeon",
    "Kalguksu", "Kong-guksu", "Ghwari-gochu-muchim", "Doraji-muchim", "Dotorimuk", "Japchae", "Kongnamul-muchim", "Hongeo-muchim", "Hoe-muchim", "Gimbap",
    "Kimchi-bokkeum-bap", "Nurungji", "Bibimbap", "Saeu-bokkeum-bap", "Albap", "Yubu-chobap", "Japgok-bap", "Jumeok-bap", "Gamja-chae-bokkeum", "Geon-saeu-bokkeum",
    "Gochujang-jinmichae-bokkeum", "Dubu-kimchi", "Tteokbokki", "Rabokki", "Myeolchi-bokkeum", "Soseji-bokkeum", "Eomuk-bokkeum", "Ojingeo-chae-bokkeum", "Jeyuk-bokkeum", "Jjuggumi-bokkeum",
    "Bossam", "Sujeonggwa", "Sikhye", "Ganjang-gejang", "Yangnyeom-gejang", "Ggaetnip-jangajji", "Tteokkochi", "Gamja-jeon", "Gyeran-mari", "Gyeran-fry",
    "Kimchi-jeon", "Donggeurangttaeng", "Saengseon-jeon", "Pa-jeon", "Hobak-jeon", "Gopchang-jeongol", "Galchi-jorim", "Gamja-jorim", "Godeungeo-jorim", "Ggongechi-jorim",
    "Dubu-jorim", "Dangkong-jorim", "Maechurial-jang-jorim", "Yeongeun-jorim", "Ueong-jorim", "Jang-jorim", "Kodari-jorim", "Jeonbok-juk", "Hobak-juk", "Kimchi-jjigae",
    "Dakgaejang", "Dongtae-jjigae", "Doenjang-jjigae", "Sundubu-jjigae", "Galbi-jjim", "Gyeran-jjim", "Kimchi-jjim", "Ggomak-jjim", "Dak-bokkeum-tang", "Suyuk",
    "Sundae", "Jokbal", "Jjimdak", "Haemul-jjim", "Galbi-tang", "Gamja-tang", "Gomtang_Seolleongtang", "Maeun-tang", "Samgye-tang", "Chueo-tang",
    "Gochu-twigim", "Saeu-twigim", "Ojingeo-twigim", "Yakgwa", "Yaksik", "Hangwa", "Meongge", "Sannakji", "Mulhoe", "Yukhoe"
]

# Label List (KOR)
LABELS_KOR = [
    "갈비구이", "갈치구이", "고등어구이", "곱창구이", "닭갈비", "더덕구이", "떡갈비", "불고기", "삼겹살", "장어구이",
    "조개구이", "조기구이", "황태구이", "훈제오리", "계란국", "떡국/만둣국", "무국", "미역국", "북엇국", "시래기국",
    "육개장", "콩나물국", "과메기", "양념치킨", "젓갈", "콩자반", "편육", "피자", "후라이드치킨", "갓김치",
    "깍두기", "나박김치", "무생채", "배추김치", "백김치", "부추김치", "열무김치", "오이소박이", "총각김치", "파김치",
    "가지볶음", "고사리나물", "미역줄기볶음", "숙주나물", "시금치나물", "애호박볶음", "경단", "꿀떡", "송편", "만두",
    "라면", "막국수", "물냉면", "비빔냉면", "수제비", "열무국수", "잔치국수", "짜장면", "짬뽕", "쫄면",
    "칼국수", "콩국수", "꽈리고추무침", "도라지무침", "도토리묵", "잡채", "콩나물무침", "홍어무침", "회무침", "김밥",
    "김치볶음밥", "누룽지", "비빔밥", "새우볶음밥", "알밥", "유부초밥", "잡곡밥", "주먹밥", "감자채볶음", "건새우볶음",
    "고추장진미채볶음", "두부김치", "떡볶이", "라볶이", "멸치볶음", "소시지볶음", "어묵볶음", "오징어채볶음", "제육볶음", "쭈꾸미볶음",
    "보쌈", "수정과", "식혜", "간장게장", "양념게장", "깻잎장아찌", "떡꼬치", "감자전", "계란말이", "계란후라이",
    "김치전", "동그랑땡", "생선전", "파전", "호박전", "곱창전골", "갈치조림", "감자조림", "고등어조림", "꽁치조림",
    "두부조림", "땅콩조림", "메추리알장조림", "연근조림", "우엉조림", "장조림", "코다리조림", "전복죽", "호박죽", "김치찌개",
    "닭개장", "동태찌개", "된장찌개", "순두부찌개", "갈비찜", "계란찜", "김치찜", "꼬막찜", "닭볶음탕", "수육",
    "순대", "족발", "찜닭", "해물찜", "갈비탕", "감자탕", "곰탕/설렁탕", "매운탕", "삼계탕", "추어탕",
    "고추튀김", "새우튀김", "오징어튀김", "약과", "약식", "한과", "멍게", "산낙지", "물회", "육회"
]

MODEL_PATH = "yolo/best.pt" # Path에 맞게 설정
model = YOLO(MODEL_PATH)  # Load Model

def run_detection(img_path, save_path=None, json_save_path=None, conf_thres=0.5): # Save bounding boxed image
    results = model(img_path, conf=conf_thres)[0]
    img = cv2.imread(img_path)
    detected = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        score = float(box.conf[0])
        label_eng = LABELS_ENG[cls_id]
        label_kor = LABELS_KOR[cls_id]

        if save_path: # Box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.putText(img, f"{label_eng} {score:.2f}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 255), 2)

        detected.append({ # Save
            # "class_index": cls_id,
            # "label_eng": label_eng,
            "label_kor": label_kor,
            "confidence": round(score, 4)
        })

    if save_path:
        cv2.imwrite(save_path, img)
        print(f"✅ 분석 이미지 저장됨: {save_path}")

    if json_save_path:
        with open(json_save_path, "w", encoding="utf-8") as f:
            json.dump(detected, f, ensure_ascii=False, indent=2)
        print(f"📄 JSON 저장 완료: {json_save_path}")

    return detected

if __name__ == "__main__": # python detect.py --img test.png --save_path path/filename
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--img', type=str, required=True, help='Input image path')
    parser.add_argument('--conf', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--save_path', type=str, default=None, help='Output image path with boxes')  # ✅ 추가

    args = parser.parse_args()

    result = run_detection(args.img, save_path=args.save_path, conf_thres=args.conf)  # ✅ 반영
    print(json.dumps(result, ensure_ascii=False, indent=2))

