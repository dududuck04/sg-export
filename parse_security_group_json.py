#!/usr/bin/python
# -*- coding:utf-8 -*-
import json
from pprint import pprint
import sys
import os

def calculate_securitygroup(print_name, rule_array, is_inbound):
    print(print_name)
    rule_dict={}
    for object in rule_array:
        IpProtocol=object["IpProtocol"]
        port=""

        if IpProtocol == "-1":
            IpProtocol="All traffic"
            port="All"
        else:
            if "ToPort" in object:
                port=str(object["ToPort"])
            if "FromPort" in object:
                fromPort = str(object["FromPort"])
                if fromPort != port:
                    port = fromPort + "-" + port

        if IpProtocol == "tcp":
            IpProtocol = "TCP"
        elif IpProtocol == "udp":
            IpProtocol = "UDP"
        for group_object in object["UserIdGroupPairs"]:
            group_id = ""
            description = ""
            if "GroupId" in group_object:
                group_id = group_object["GroupId"]
            if "Description" in group_object:
                description = group_object["Description"]
            rule = {"IpProtocol" : IpProtocol, "group_id": group_id, "port": port, "description": description, "inbound": is_inbound}
            rule_dict[group_id + "/" + port] = rule

        for group_object in object["IpRanges"]:
            cidr_block = ""
            description = ""
            if "CidrIp" in group_object:
                cidr_block = group_object["CidrIp"]
            if "Description" in group_object:
                description = group_object["Description"]
            rule = {"IpProtocol" : IpProtocol, "group_id": cidr_block, "port": port, "description": description, "inbound": is_inbound}
            rule_dict[cidr_block + "/" + port] = rule

        for prefix_object in object["PrefixListIds"]:
            cidr_block = ""
            description = ""
            if "PrefixListId" in prefix_object:
                cidr_block = prefix_object["PrefixListId"]
            if "Description" in prefix_object:
                description = prefix_object["Description"]
            rule = {"IpProtocol" : IpProtocol, "group_id": cidr_block, "port": port, "description": description, "inbound": is_inbound}
            rule_dict[cidr_block + "/" + port] = rule

    for k,v in sorted(rule_dict.items()):
        description = v["description"]
        change_description = description.replace(" ", "__")
        if v["inbound"]:
            print(v["IpProtocol"] + "," + v["group_id"] + " / " + v["port"] + ",," + change_description)
        else:
            print(v["IpProtocol"] + ",," + v["group_id"] + " / " + v["port"] + "," + change_description)

if __name__ == "__main__":
    file_path=os.path.dirname(os.path.abspath(__file__)) + "/" + sys.argv[1]
    if os.path.exists(file_path):
        json_data=open(file_path).read()
        data=json.loads(json_data)
        sg_name=data['SecurityGroups'][0]['GroupName']
        sg_id=data['SecurityGroups'][0]['GroupId']
        print(sg_id + " (" + sg_name + ")")
        inbound_array=data['SecurityGroups'][0]['IpPermissions']
        outbound_array=data['SecurityGroups'][0]['IpPermissionsEgress']
        calculate_securitygroup("Inbound", inbound_array, True)
        calculate_securitygroup("Outbound", outbound_array, False)
