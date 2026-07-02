import pdfplumber

# Read auth section (pages around 10-12 where auth was mentioned)
with pdfplumber.open(r'C:\Users\richg\Desktop\API 매뉴얼\API 매뉴얼\OwnerclanAPI_Seller_Manual.pdf') as pdf:
    # Search all pages for auth-related content
    for i, page in enumerate(pdf.pages):
        txt = page.extract_text()
        if txt and ('auth' in txt.lower() or 'token' in txt.lower() or 'jwt' in txt.lower() or 'login' in txt.lower()):
            print(f'--- PAGE {i+1} ---')
            print(txt)
            print()
