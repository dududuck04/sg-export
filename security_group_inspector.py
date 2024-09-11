import boto3
import pandas as pd
from datetime import datetime

class security_groups:
    def __init__(self, ec2_service, type):
        self.ec2_service = ec2_service
        self.type = type

    def describe_securities(self, name, value):
        response = self.ec2_service.describe_security_groups(Filters=[{'Name': name, 'Values': [value]}])
        return response['SecurityGroups']

    def describe_name(self, sg_id):
        try:
            response = self.ec2_service.describe_security_groups(GroupIds=[str(sg_id)])
            return response['SecurityGroups'][0].get('GroupName')
        except:
            return ''

    def describe_sg_ids(self, vpc_id):
        response = self.describe_securities('vpc-id', vpc_id)
        return [secid['GroupId'] for secid in response]

    def get_ip_ranges(self, sg_id, group_name, ip_permissions, ip_permissions_num):
        result = []
        if ip_permissions_num > 0:
            for permissions in ip_permissions:
                protocol_type = ''
                port_range = ''
                sources = ''
                description = ''
                protocol = permissions['IpProtocol']
                if protocol == '-1':
                    port_range, protocol = 'ALL', 'ALL'
                    protocol_type = 'ALL Traffic'
                if 'FromPort' in permissions:
                    from_port = permissions['FromPort']
                    to_port = permissions['ToPort']
                    port_range = f"{from_port}-{to_port}" if from_port != to_port else str(from_port)
                    protocol_type = self.get_protocol_type(protocol, from_port)
                if permissions['IpRanges']:
                    for j in permissions['IpRanges']:
                        sources = j.get('CidrIp', 'No source')
                        description = j.get('Description', '')
                        result.append((sg_id, group_name, protocol_type, protocol, port_range, sources, description))
                if permissions['UserIdGroupPairs']:
                    for i in permissions['UserIdGroupPairs']:
                        sources = self.describe_name(i['GroupId']) + ' (' + i['GroupId'] + ')'
                        description = i.get('Description', '')
                        result.append((sg_id, group_name, protocol_type, protocol, port_range, sources, description))
                if permissions['PrefixListIds']:
                    for i in permissions['PrefixListIds']:
                        sources = i.get('PrefixListId', '')
                        description = i.get('Description', '')
                        result.append((sg_id, group_name, protocol_type, protocol, port_range, sources, description))
        else:
            result.append((sg_id, group_name, '', '', '', '', ''))
        return result

    def get_protocol_type(self, protocol, port):
        protocol_map = {
            80: 'HTTP(80)',
            443: 'HTTPS',
            389: 'LDAP',
            465: 'SMTPS',
            993: 'IMAPS',
            1433: 'MSSQL',
            2049: 'NFS',
            3306: 'MYSQL/Aurora',
            3389: 'RDP',
            5439: 'RedShift',
            5432: 'PostgreSQL',
            1521: 'ORACLE',
            110: 'POP3',
            143: 'IMAP',
            22: 'SSH(22)',
        }
        return protocol_map.get(port, 'Custom TCP Rule' if protocol == 'tcp' else 'Custom UDP Rule')

    def describe_ips(self, vpc_id):
        result = []
        sg_ids = self.describe_sg_ids(vpc_id)
        for sg in sg_ids:
            sg_info = self.describe_securities('group-id', sg)
            for sg_list in sg_info:
                group_name = sg_list.get('GroupName', '')
                if self.type == 'in':
                    get_permissions = self.get_ip_ranges(sg, group_name, sg_list.get('IpPermissions', []), len(sg_list.get('IpPermissions', [])))
                else:
                    get_permissions = self.get_ip_ranges(sg, group_name, sg_list.get('IpPermissionsEgress', []), len(sg_list.get('IpPermissionsEgress', [])))
                result.extend(get_permissions)
        return result

def get_security_group_info(ec2, vpc_id, type):
    security = security_groups(ec2, type)
    return security.describe_ips(vpc_id)

def set_excel_info(first_type, label, value, sheet_name, n_sheet_name, excel_info, worksheet, start_row):
    workbook = excel_info.book
    # -----------------xlsx 디자인 용 -----------------------------
    # format to apply to xlsx
    all_format = workbook.add_format({
        'font_size': 10
    })
    # format to apply to xlsx
    border_format = workbook.add_format({
        'border': 1,
        'font_size': 10
    })
    # 최상위
    h_header_format = workbook.add_format({
        'bold': 1,
        'align': 'left',
        'font_size': 10
    })
    # 중앙정렬 format
    center_format = workbook.add_format({
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10,
        'text_wrap': True
    })
    # 헤더 배경 + 글씨 format
    header_format = workbook.add_format({
        'bold': 1,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_color': 'white',
        'font_size': 10,
        'bg_color': '#9d9d9d'
    })
    # A라인 bold 처리
    bold_format = workbook.add_format({
        'bold': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 10
    })

    #-----------excel_set--------------
    df_info = pd.DataFrame.from_records(value, columns=label)
    df_info.index += 1
    df_info.to_excel(excel_info, sheet_name=sheet_name, startrow=start_row)
    if first_type:
        worksheet = excel_info.sheets[sheet_name]
        worksheet.write(0, 0, sheet_name, h_header_format)
    worksheet.write(start_row - 1, 0, n_sheet_name, h_header_format)
    worksheet.write(start_row, 0, '연번')

    st_row = start_row
    ed_row = st_row + len(df_info)

    # 포멧 설정
    # A라인 bold 처리
    worksheet.set_column('A:A', 18, bold_format)
    # 중앙 정렬
    worksheet.set_column('B:P', 18, center_format)
    # 헤더 색,배경
    worksheet.conditional_format(st_row, 0, st_row, len(label), {
        'type': 'cell',
        'criteria': 'not equal to',
        'value': '"XX"',
        'format': header_format})
    # 출력값
    worksheet.conditional_format(st_row, 0, ed_row, len(label), {
        'type': 'cell',
        'criteria': 'not equal to',
        'value': '"XX"',
        'format': border_format})

    start_row += len(df_info) + 3

    return worksheet, start_row

def main():
    try:
        # 기본 환경 설정
        vpc_id = ""
        region = ""
        access_key = ""
        secret_key = ""
        session_token = ""

        session = boto3.Session(region_name=region, aws_access_key_id=access_key, aws_secret_access_key=secret_key, aws_session_token=session_token)
        ec2 = session.client('ec2', region_name=region)

        # 보안 그룹 정보 수집
        security_groups_info_inbound = get_security_group_info(ec2, vpc_id, 'in')
        security_groups_info_outbound = get_security_group_info(ec2, vpc_id, 'out')

        # 엑셀에 데이터 저장
        file_name = f"security_groups_{vpc_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        excel_file_path = file_name
        writer = pd.ExcelWriter(excel_file_path, engine='xlsxwriter')
        workbook = writer.book

        # Inbound 보안 그룹 규칙 저장
        sg_inbound_labels = ['ID', 'Name', 'Type', 'Protocol', 'Port Range', 'Source', 'Description']
        worksheet_sg_inbound, start_row = set_excel_info(True, sg_inbound_labels, security_groups_info_inbound, 'Security Groups', 'Inbound Rules', writer, None, 3)

        # Outbound 보안 그룹 규칙 저장
        sg_outbound_labels = ['ID', 'Name', 'Type', 'Protocol', 'Port Range', 'Destination', 'Description']
        worksheet_sg_outbound, start_row = set_excel_info(False, sg_outbound_labels, security_groups_info_outbound, 'Security Groups', 'Outbound Rules', writer, worksheet_sg_inbound, start_row + 3)

        writer.close()

        print(f"보안 그룹 정보가 {excel_file_path}에 저장되었습니다.")

    except Exception as e:
        print(f"오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    main()
