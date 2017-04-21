# -*- coding: utf-8 -*-
import re
"""
Automatically calculate the Cut Duration on Shots when the Cut In or Cut Out value is changed.

Conversely, this example does not make any updates to Cut In or Cut Out values if the Cut Duration field
is modified. You can modify that logic and/or the field names to match your specific workflow.
"""


def registerCallbacks(reg):
    matchEvents = {'Shotgun_Shot_Change': ['code']}

    reg.registerCallback("shotgunEventDaemon", "0d1f24f9665ef2771150e496ac5f293844275dadc63707bbb0bb652d12c6983e",
    calculateShotName, matchEvents, None)


def calculateShotName(sg, logger, event, args):
    meta_data = event['meta']
    if 'new_value' not in meta_data:
        return
    pattern = r"c\d{1,3}[a-z]?"
    old_value = meta_data["new_value"]
    if not re.match(pattern, old_value):
        return
    filters = [["id", "is", meta_data["entity_id"]]]
    fields = ["sg_sequence", "code"]
    current_shot_info = sg.find_one("Shot", filters, fields)
    print current_shot_info
    sequence = current_shot_info["sg_sequence"]
    print sequence
    if not sequence:
        return
    new_value = "%s_%s" % (sequence["name"], old_value)
    sg.update("Shot", current_shot_info["id"], {'code': new_value})
    logger.info("%s: code rename to %s" % (current_shot_info['code'], new_value))

