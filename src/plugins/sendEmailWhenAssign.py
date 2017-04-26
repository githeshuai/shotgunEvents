# -*- coding: utf-8 -*-
"""
send email when assign to somebody
"""
from email.header import Header
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import smtplib


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((
        Header(name, 'utf-8').encode(),
        addr.encode('utf-8') if isinstance(addr, unicode) else addr))


def send_email(from_addr, password, to_addr, header, message, smtp_server='192.168.0.211'):
    msg = MIMEMultipart()
    msg.attach(MIMEText(message, 'plain', 'utf-8'))
    msg['From'] = _format_addr(from_addr)
    msg['To'] = _format_addr(to_addr)
    msg['Subject'] = Header(header, 'utf-8').encode()

    server = smtplib.SMTP(smtp_server, 25)
    # server.set_debuglevel(1)
    # server.login(from_addr, password)
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()


def get_user_email(sg, user_id):
    user_info = sg.find_one("HumanUser", [["id", "is", user_id]], ["email"])
    email_address = user_info["email"]
    return email_address


def get_leader(sg, user_info):
    user_filter = [["id", "is", user_info["id"]]]
    user = sg.find_one("HumanUser", user_filter, ["department"])
    if not user. has_key("department"):
        return
    user_dep_info = user["department"]
    user_dep_name = user_dep_info["name"]
    leader_dep_name = "%sLeader" % user_dep_name
    leaders = sg.find("HumanUser", [["department", "name_is", leader_dep_name]], ["email", "name"])
    return leaders


def registerCallbacks(reg):
    matchEvents = {'Shotgun_Task_Change': ['task_assignees']}

    reg.registerCallback("shotgunEventDaemon", "0d1f24f9665ef2771150e496ac5f293844275dadc63707bbb0bb652d12c6983e",
    send_email_when_assign, matchEvents, None)


def send_email_when_assign(sg, logger, event, args):
    sender = event["user"]
    sender_email = get_user_email(sg, sender["id"])
    meta_data = event["meta"]
    added = meta_data["added"]
    removed = meta_data["removed"]
    if not added and not removed:
        return
    filters = [["id", "is", meta_data["entity_id"]]]
    fields = ["content", "sg_status_list", "sg_priority_1", "step.Step.short_name", "entity.Asset.sg_asset_type",
              "entity.Asset.code", "entity.Shot.sg_sequence", "entity.Shot.code", "entity"]
    task_info = sg.find_one("Task", filters, fields)
    logger.info(task_info)
    step = task_info["step.Step.short_name"]
    task_name = task_info["content"]
    status = task_info["sg_status_list"]
    priority = task_info["sg_priority_1"]
    if task_info["entity"]["type"] == "Asset":
        asset_type = task_info["entity.Asset.sg_asset_type"]
        asset_name = task_info["entity.Asset.code"]
        task_str = "Asset Type: %s\n Asset Name: %s\n Step: %s\n Task: %s\nStatus: %s\nPriority: %s" % \
                   (asset_type, asset_name, step, task_name, status, priority)
    else:
        sequence = task_info["entity.Shot.sg_sequence"]["name"]
        shot = task_info["entity.Shot.code"]
        task_str = "Sequence: %s\n Shot: %s\nStep: %s\n Task: %s\nStatus: %s\nPriority: %s" % \
                   (sequence, shot, step, task_name, status, priority)
    if added:
        for user in added:
            sg.follow(user, task_info)
            email_address = get_user_email(sg, user["id"])
            send_email(sender_email, "123456", email_address, u"新任务提醒", u"你有新任务:\n\n%s" % task_str)
            logger.info("send email to %s" % user["name"])
            leaders = get_leader(user)
            if not leaders:
                logger.warning("No leader found of %s" % user["name"])
                return
            for leader in leaders:
                email_add = leader["email"]
                sg.follow(leader, task_info)
                send_email(sender_email, "123456", email_add, u"组员新任务提醒", u"有任务分配给%s\n%s" % (user["name"], task_str))
    if removed:
        for user in removed:
            email_address = get_user_email(sg, user["id"])
            send_email(sender_email, "123456", email_address, u"取消任务提醒", u"任务:\n\n%s\n\n不用你做的，恭喜！" % task_str)
            logger.info("send email to %s" % user["name"])
