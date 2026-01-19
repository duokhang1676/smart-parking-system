import PyPDF2
import win32print
import win32ui
from datetime import datetime
from win32con import *


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode import code128

def write_file_pdf(date,license,time_in,time_out,parking_time,total_price):
    # Dữ liệu cần in
    # Lấy ngày tháng năm hiện tại

    text = f"""\
    
    BÃI ĐỖ XE TRƯỜNG ĐẠI HỌC CÔNG NGHIỆP TP.HCM
    ĐC: 12 Nguyễn Văn Bảo, P4, Gò Vấp, HCM
    ĐT: 0123456789
    ------------------------------------------------------------------------------
              VÉ THU TIỀN ĐẬU XE Ô TÔ
    -
    Loại: Xe ô tô từ 4 đến 8 chỗ
    Ngày: {date}
    Số xe: {license}
    Giờ vào: {time_in.replace(microsecond=0)}
    Giờ ra: {time_out.replace(microsecond=0)}
    Thời gian đỗ: {parking_time} giờ
    ------------------------------------------------------------------------------
    GIÁ TIỀN:   {total_price:,} ĐỒNG
    -
                    (Đã bao gồm thuế GTGT 10%)
    """

    # Đường dẫn file PDF muốn tạo
    file_path = "app/resources/print_bill/receipt.pdf"

    # Đường dẫn đến font Arial Unicode MS TTF
    font_path = "app/resources/print_bill/arial-unicode-ms.ttf"  # Thay bằng đường dẫn thực tế đến font Arial Unicode MS TTF

    # Đăng ký font Arial Unicode MS
    pdfmetrics.registerFont(TTFont('ArialUnicodeMS', font_path))
    # Tạo đối tượng canvas để vẽ vào PDF
    c = canvas.Canvas(file_path, pagesize=letter)

    # Thiết lập font chữ và kích thước
    c.setFont("ArialUnicodeMS", 12)

    # Vị trí bắt đầu
    x, y = 30, 750  # Vị trí bắt đầu ở góc trên bên trái

    # In nội dung vào PDF
    lines = text.split("\n")
    for line in lines:
        c.drawString(x, y, line)  # In từng dòng
        y -= 14  # Giảm y để xuống dòng tiếp theo

    # # Tạo mã vạch (Barcode) Code128
    # barcode_value = "123456789012"
    # barcode = code128.Code128(barcode_value)
    # barcode_x = 30  # Vị trí x cho mã vạch
    # barcode_y = y   # Vị trí y cho mã vạch, cách dòng cuối một chút
    # # Vẽ mã vạch vào canvas
    # barcode.drawOn(c, barcode_x, barcode_y)

    # Lưu PDF
    c.save()

    # print(f"PDF đã được tạo thành công tại: {file_path}")



# Đọc file PDF và trích xuất văn bản
def extract_text_from_pdf(pdf_file_path):
    text = ""
    with open(pdf_file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n"
    return text
def printting():
    # Chọn máy in mặc định
    printer_name = win32print.GetDefaultPrinter()

    # Mở kết nối đến máy in
    printer = win32ui.CreateDC()
    printer.CreatePrinterDC(printer_name)

    # Bắt đầu in
    printer.StartDoc("PDF Document")
    printer.StartPage()

    # Đọc văn bản từ file PDF
    pdf_file_path = "app/resources/print_bill/receipt.pdf"
    text = extract_text_from_pdf(pdf_file_path)

    # Vị trí bắt đầu
    x, y = 10, 10

    # In văn bản trích xuất từ PDF
    lines = text.split("\n")

    # Thiết lập font chữ
    font = win32ui.CreateFont({
        "name": "Arial",       # Tên font
        "height": 24,          # Kích thước font
        "weight": FW_NORMAL,   # Đặt font bình thường
    })
    font2 = win32ui.CreateFont({
        "name": "Arial",       # Tên font
        "height": 32,          # Kích thước font
        "weight": FW_NORMAL,   # Đặt font bình thường
    })
    # Sử dụng font đã tạo
    printer.SelectObject(font)

    # In từng dòng văn bản, tăng giá trị y sau mỗi dòng
    for i,line in enumerate(lines):
        if i == 5 or i == 14:
            printer.SelectObject(font2)
            printer.TextOut(x, y, line)
            printer.SelectObject(font)
        else:       
            printer.TextOut(x, y, line)
        y += 30  # Tăng y sau mỗi dòng để xuống dòng

    # Kết thúc và in xong
    printer.EndPage()
    printer.EndDoc()

    # Đóng kết nối
    printer.DeleteDC()