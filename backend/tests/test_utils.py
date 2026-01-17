from app.utils.algeria_utils import validate_wilaya, format_dz_phone

def test_validate_wilaya():
    assert validate_wilaya("16") == True
    assert validate_wilaya("58") == True
    assert validate_wilaya("59") == False
    assert validate_wilaya("00") == False
    assert validate_wilaya("abc") == False

def test_format_dz_phone():
    assert format_dz_phone("0550123456") == "+213550123456"
    assert format_dz_phone("550123456") == "+213550123456"
    assert format_dz_phone("+213550123456") == "+213550123456"
