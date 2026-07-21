"""gateways/ — интерфейсы к внешним системам (1С, OCR, CAD)."""
from .one_c_gateway import (  # noqa
    OneCGateway, FileGateway, HttpGateway,
    OneCItem, OneCMaterial, OneCEquipment, OneCProfession, OneCResourceSpec,
    get_gateway, reset_gateway,
)
