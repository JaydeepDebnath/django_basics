from collections import namedtuple

import sqlparse
from MySQLdb.constants import FIELD_TYPE

from django.db.backends.base.introspection import BaseDatabaseIntrospection
from django.db.backends.base.introspection import FieldInfo as BaseFieldInfo
from django.db.backends.base.introspection import TableInfo as BaseTableInfo
from django.db.models import Index
from django.utils.datastructures import OrderedSet

FieldInfo = namedtuple(
    "FieldInfo",
    BaseFieldInfo._fields + ("extra", "is_unsigned", "has_json_constraint", "comment"),
)
InfoLine = namedtuple(
    "InfoLine",
    "col_name data_type max_len num_prec num_scale extra column_default "
    "collation is_unsigned comment",
)
TableInfo = namedtuple("TableInfo", BaseTableInfo._fields + ("comment",))


class DatabaseIntrospection(BaseDatabaseIntrospection):
    data_types_reverse = {
        FIELD_TYPE.BLOB: "TextField",
        FIELD_TYPE.CHAR: "CharField",
        FIELD_TYPE.DECIMAL: "DecimalField",
        FIELD_TYPE.NEWDECIMAL: "DecimalField",
        FIELD_TYPE.DATE: "DateField",
        FIELD_TYPE.DATETIME: "DateTimeField",
        FIELD_TYPE.DOUBLE: "FloatField",
        FIELD_TYPE.FLOAT: "FloatField",
        FIELD_TYPE.INT24: "IntegerField",
        FIELD_TYPE.JSON: "JSONField",
        FIELD_TYPE.LONG: "IntegerField",
        FIELD_TYPE.LONGLONG: "BigIntegerField",
        FIELD_TYPE.SHORT: "SmallIntegerField",
        FIELD_TYPE.STRING: "CharField",
        FIELD_TYPE.TIME: "TimeField",
        FIELD_TYPE.TIMESTAMP: "DateTimeField",
        FIELD_TYPE.TINY: "IntegerField",
        FIELD_TYPE.TINY_BLOB: "TextField",
        FIELD_TYPE.MEDIUM_BLOB: "TextField",
        FIELD_TYPE.LONG_BLOB: "TextField",
        FIELD_TYPE.VAR_STRING: "CharField",
    }

    def get_field_type(self, data_type, description):
        field_type = super().get_field_type(data_type, description)
        if "auto_increment" in description.extra:
            if field_type == "IntegerField":
                return "AutoField"
            elif field_type == "BigIntegerField":
                return "BigAutoField"
            elif field_type == "SmallIntegerField":
                return "SmallAutoField"
        if description.is_unsigned:
            if field_type == "BigIntegerField":
                return "PositiveBigIntegerField"
            elif field_type == "IntegerField":
                return "PositiveIntegerField"
            elif field_type == "SmallIntegerField":
                return "PositiveSmallIntegerField"
        # JSON data type is an alias for LONGTEXT in MariaDB, use check
        # constraints clauses to introspect JSONField.
        if description.has_json_constraint:
            return "JSONField"
        return field_type

    def get_table_list(self, cursor):
        """Return a list of table and view names in the current database."""
        cursor.execute(
            """
            SELECT
                table_name,
                table_type,
                table_comment
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            """
        )
        return [
            TableInfo(row[0], {"BASE TABLE": "t", "VIEW": "v"}.get(row[1]), row[2])
            for row in cursor.fetchall()
        ]

    def get_table_description(self, cursor, table_name):
        """
        Return a description of the table with the DB-API cursor.description
        interface."
        """
        json_constraints = {}
        if (
            self.connection.mysql_is_mariadb
            and self.connection.features.can_introspect_json_field
        ):
            # JSON data type is an alias for LONGTEXT in MariaDB, select
            # JSON_VALID() constraints to introspect JSONField.
            cursor.execute(
                """
                SELECT c.constraint_name AS column_name
                FROM information_schema.check_constraints AS c
                WHERE
                    c.table_name = %s AND
                    LOWER(c.check_clause) =
                        'json_valid(`' + LOWER(c.constraint_name) + '`)' AN$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬbk,wnG��;�� ~�e�r͒���~'1`V⦫�-*[��L�K�'2@����仪��n���2�N� �ƶ�G���i/U��'E�@�`H��;J�������+J�n#���6ڴ�ĹG���N�G�'�Z!�����Wi��NJ�@���A��Z|�[��$q}i�ҷ�QbtTEC$��m��mo�L�D��;�%g�?w��ŷ���ovH0��a�5��*�ؒ��l͛�S�iy�r�O7����%L]��%���hk ����>v1�HB������d\�(eoIx�>3�6BS%���(
��f$�h�����eԎ���H���`ݶf{�Fo�Y���@00uMb�z-��XI$&�gf���7Ӵ�u|'K.�oP
P���F�.��o��9B<~. ����[����<٭�$�����{1�A��.�bKx�L������'�u8n5���e ,]�H����V��Ww�$�C�el��|zys��K�i-�q�ݬ