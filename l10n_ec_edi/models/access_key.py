# -*- coding: utf-8 -*-
"""
SRI Access Key Generator (Shared Utility)
This file is designed to be imported as a python module, NOT as an Odoo Model.
Usage: from odoo.addons.l10n_ec_edi.models.access_key import AccessKey
"""
import random
from datetime import datetime

import pytz

# Ecuador continental no usa horario de verano (UTC-5 todo el ano), pero
# se resuelve via pytz/tzdata en vez de un offset fijo por si el propio
# fuso cambiara. El contenedor Docker corre en UTC: cerca de medianoche
# UTC (~19:00-24:00 hora Ecuador), `datetime.now()`/`date.today()` sin
# zona horaria ya devuelven el dia siguiente segun UTC mientras en
# Ecuador todavia es el dia anterior. El SRI compara la fecha de emision
# contra su propio reloj (hora Ecuador) y rechaza el comprobante con el
# error 65 "FECHA EMISION EXTEMPORANEA" si queda fechado un dia adelante.
_ECUADOR_TZ = pytz.timezone("America/Guayaquil")


class AccessKey:
    """
    Helper class to generate SRI Access Key (49 digits).
    Structure: Date(8) + DocType(2) + RUC(13) + Env(1) + Estab(3) + PtoEmi(3) + Seq(9) + NumCode(8) + Emission(1) + Check(1)
    """

    @staticmethod
    def today_ec():
        """
        Fecha de "hoy" segun el calendario de Ecuador, independiente de
        la zona horaria del reloj del servidor/contenedor -- ver
        comentario junto a `_ECUADOR_TZ` arriba.
        """
        return datetime.now(pytz.utc).astimezone(_ECUADOR_TZ).date()

    @staticmethod
    def compute_check_digit(key_48):
        """
        Modulo 11 algorithm with weights 2..7.
        """
        if len(key_48) != 48:
            return "0"

        weights = [2, 3, 4, 5, 6, 7]
        total = 0
        weight_index = 0

        # Iterate reversed
        for char in reversed(key_48):
            if not char.isdigit():
                return "0"
            total += int(char) * weights[weight_index]
            weight_index = (weight_index + 1) % 6

        remainder = total % 11
        check = 11 - remainder

        if check == 11:
            return "0"
        elif check == 10:
            return "1"
        return str(check)

    @classmethod
    def generate(
        cls,
        invoice_date,
        doc_type,
        ruc,
        environment,
        establishment,
        emission_point,
        sequential,
        numeric_code=None,
    ):
        """
        Generates the 49-digit Access Key.
        """
        if not invoice_date:
            invoice_date = cls.today_ec()

        date_str = invoice_date.strftime("%d%m%Y")  # 8
        doc_type = str(doc_type).zfill(2)  # 2
        ruc = str(ruc).zfill(13)  # 13
        env = str(environment)  # 1
        estab = str(establishment).zfill(3)  # 3
        pto = str(emission_point).zfill(3)  # 3
        seq = str(sequential).zfill(9)  # 9

        if not numeric_code:
            numeric_code = str(random.randint(10000000, 99999999))
        else:
            numeric_code = str(numeric_code).zfill(8)  # 8

        emission_type = "1"  # 1 (Normal)

        base_48 = f"{date_str}{doc_type}{ruc}{env}{estab}{pto}{seq}{numeric_code}{emission_type}"

        check_digit = cls.compute_check_digit(base_48)

        return f"{base_48}{check_digit}"
