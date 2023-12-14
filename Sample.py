from pdf2image import convert_from_path
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import pytesseract
import cv2

pages = convert_from_path('data/sample-split.pdf', 500)

def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

results = []
sl, name, voter, father, mother, occupation, birthday, address, thana, union, ward, voterArea, voterAreaNo = [],[],[],[],[],[],[],[],[],[],[],[],[]

for num,page in enumerate(pages):
    page.save('temp/pages/'+str(num) + '.jpg','JPEG')
    
for i in range(num-2): # (num-2) is besause, we have escaped first 2 pages
    image_file = f'temp/pages/{i+2}.jpg'
    img = cv2.imread(image_file)
    gray_image = grayscale(img)
    cv2.imwrite("temp/gray.jpg", gray_image)
    thresh, im_bw = cv2.threshold(gray_image, 180, 120, cv2.THRESH_BINARY)
    cv2.imwrite("temp/bw_image.jpg", im_bw)
    blur = cv2.GaussianBlur(im_bw, (5,5), 0)
    cv2.imwrite("temp/index_blur.jpg", blur)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    cv2.imwrite("temp/index_thresh.jpg", thresh)
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[2]
    cnts = sorted(cnts, key=lambda x: cv2.boundingRect(x)[0])
    
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if h > 20 and w > 600 and h < 600:
            common_list = []
            roiC = im_bw[y+3:y+h-4, x+3:x+w-3]
            cv2.rectangle(img, (x, y), (x+w, y+h), (369, 255, 12), 2)
            ocr = pytesseract.image_to_string(roiC, lang='ben')
            ocr = ocr.split("\n")
            ocr = [item for item in ocr if item != '']
            del ocr[0]
            common_list.append(ocr[0].split(" ")[-1])
            common_list.append(ocr[1].split("ইউনিয়ন")[0].split(':')[1])
            common_list.append(ocr[1].split(':')[-1])
            common_list.append(ocr[2].split("পোষ্টকোড")[0].split(':')[-1])
            common_list.append(ocr[3].split(':')[-1].replace(' ', ''))
            
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if h > 20 and w < 600:
            filtered_list = []
            roi = im_bw[y+3:y+h-4, x+3:x+w-3]
            cv2.rectangle(im_bw, (x, y), (x+w, y+h), (36, 255, 12), 1)
            ocr_result = pytesseract.image_to_string(roi, lang='ben')
            ocr_result = ocr_result.split("\n")
            ocr_result = [item for item in ocr_result if item != '']
            print(ocr_result)
            
            filtered_list.append(ocr_result[0].split('নাম')[0].replace(' ', '').replace('.', ''))
            
            filtered_list.append(ocr_result[0].split('নাম')[1].replace(':', '').replace(';', ''))
            
            filtered_list.append(ocr_result[1].split('ভোটার নং')[1].replace(':', ''))
            
            if 'পিতা' in ocr_result[2]:
                filtered_list.append(ocr_result[2].split('পিতা')[1].replace(':', '').replace(';', ''))
            else:
                ocr_result[2] = ocr_result[2].replace(ocr_result[2].split(' ')[0], 'পিতা')
                filtered_list.append(ocr_result[2].replace('পিতা', '').replace(':', '').replace(';', ''))
                
            if 'মাতা' in ocr_result[3]:
                filtered_list.append(ocr_result[3].split('মাতা')[1].replace(':', '').replace(';', ''))
            else:
                ocr_result[3] = ocr_result[3].replace(ocr_result[3].split(' ')[0], 'মাতা')
                filtered_list.append(ocr_result[3].replace('মাতা', '').replace(':', '').replace(';', ''))    
                        
            filtered_list.append(''.join(ocr_result[4].split(' তারিখ')[0].replace('পেশা', '').replace(':', '').replace(';', ''))[:-4])
            
            filtered_list.append(ocr_result[4].split(' তারিখ')[1].replace(':', '').replace(';', ''))
            
            address = ''
            for i in range(len(ocr_result)-5):
                address = address + ocr_result[5+i]
            filtered_list.append(address.replace(':', '').replace('ঠিকানা', ''))
                
            results.append(filtered_list)
            
    for i in range(len(results)):
        sl.append(results[i][0])
        name.append(results[i][1])
        voter.append(results[i][2])
        father.append(results[i][3])
        mother.append(results[i][4])
        occupation.append(results[i][5])
        birthday.append(results[i][6])
        address.append(results[i][7])
        thana.append(common_list[0])
        union.append(common_list[1])
        ward.append(common_list[2])
        voterArea.append(common_list[3])
        voterAreaNo.append(common_list[4])
        
data = {
    "SL No": sl,
    "Name": name,
    "Voter No": voter,
    "Father": father,
    "Mother": mother,
    "Occupation": occupation,
    "Birthday": birthday,
    "Address": address,
    "Upojilla/Thana": thana,
    "Union/Ward": union,
    "Ward No": ward,
    "Voter Area": voterArea,
    "Voter Area No.": voterAreaNo
}

df = pd.DataFrame(data)

# SQLite database connection
engine = create_engine('sqlite:///output_database.db', echo=True)

# Save the DataFrame to a SQL database
df.to_sql('voters', con=engine, index=False, if_exists='replace')

# Print the first few rows of the SQL table
print(pd.read_sql_query('SELECT * FROM voters', con=engine))

    