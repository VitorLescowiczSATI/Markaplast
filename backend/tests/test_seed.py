from app.services.seed import derivar_atributos


def test_deriva_litros_e_modelo():
    a = derivar_atributos("5L M2")
    assert a["capacidade"] == "5L"
    assert a["modelo"] == "M2"
    assert a["alca"] == "nao"


def test_deriva_sem_alca():
    a = derivar_atributos("1L sem alça")
    assert a["capacidade"] == "1L"
    assert a["alca"] == "nao"
    assert a["modelo"] == ""


def test_deriva_com_alca():
    a = derivar_atributos("2L redondo com alça")
    assert a["alca"] == "sim"
    assert a["capacidade"] == "2L"
    assert a["modelo"] == "redondo"


def test_deriva_pote_peso():
    a = derivar_atributos("Pote de soda 300g")
    assert a["peso"] == "300g"
    assert a["modelo"] == "soda"
    assert a["capacidade"] == ""
