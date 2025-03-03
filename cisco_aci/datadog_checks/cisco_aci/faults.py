# (C) Datadog, Inc. 2025-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
# JMW copied and modified from fabric.py
# JMWDOWN
import datetime
import time

from datadog_checks.base.utils.serialization import json
from datadog_checks.base.utils.time import get_current_datetime, get_timestamp

from . import aci_metrics, exceptions, helpers, ndm

VENDOR_CISCO = 'cisco'
PAYLOAD_METADATA_BATCH_SIZE = 100
DEVICE_USER_TAGS_PREFIX = "dd.internal.resource:ndm_device_user_tags"
INTERFACE_USER_TAGS_PREFIX = "dd.internal.resource:ndm_interface_user_tags"


class Faults:
    """
    Collect faults from the APIC
    """

    def __init__(self, check, api, instance, namespace):
        self.check = check
        self.api = api
        self.instance = instance
        self.check_tags = check.check_tags
        self.namespace = namespace
        self.send_log = check.send_log

        # Config for submitting faults as log
        self.send_faults = self.instance.get('send_faults', False)

        # grab some functions from the check
        self.gauge = check.gauge
        self.rate = check.rate
        self.log = check.log
        self.submit_metrics = check.submit_metrics
        self.tagger = self.check.tagger
        self.external_host_tags = self.check.external_host_tags
        self.event_platform_event = check.event_platform_event

    def faults_enabled(self):
        return self.send_faults

    def collect(self):
        self.log.info("JMWfaults.collect()")
        # JMW use this flag for faults too?
        if self.faults_enabled():  # JMW test with both true and false
            faults = self.api.get_faults()
            # JMW? collect_timestamp = int(time.time())
            self.submit_faults(faults)

            # JMW batch faults when sending as logs?
            # JMWFABRIC batches = ndm.batch_payloads(self.namespace, devices, interfaces, links, collect_timestamp)
            # JMWFABRIC for batch in batches:
            # JMWFABRIC     self.event_platform_event(json.dumps(batch.model_dump(exclude_none=True)), "network-devices-metadata")

# sample fault
# {
#   "faultInst": {
#     "attributes": {
#       "ack": "no",
#       "alert": "no",
#       "cause": "port-down",
#       "changeSet": "adminSt:up, autoNeg:on, bw:0, delay:1, dot1qEtherType:0x8100, fcotChannelNumber:Channel32, id:po1.1, inhBw:unspecified, isReflectiveRelayCfgSupported:Supported, layer:Layer3, linkDebounce:100, linkLog:default, mdix:auto, medium:broadcast, mode:trunk, mtu:0, name:bond1, operSt:down, portT:unknown, prioFlowCtrl:auto, reflectiveRelayEn:off, routerMac:not-applicable, snmpTrapSt:enable, spanMode:not-a-span-dest, speed:inherit, switchingSt:disabled, trunkLog:default, usage:discovery",
#       "childAction": "",
#       "code": "F0104",
#       "created": "2025-02-23T19:09:31.539-03:00",
#       "delegated": "no",
#       "descr": "Bond Interface po1.1 on node 1 of fabric ACI Fabric1 with hostname apic1 is now down",
#       "dn": "topology/pod-1/node-1/sys/caggr-[po1.1]/fault-F0104",
#       "domain": "infra",
#       "highestSeverity": "critical",
#       "lastTransition": "2025-02-23T19:11:37.877-03:00",
#       "lc": "raised",
#       "occur": "1",
#       "origSeverity": "critical",
#       "prevSeverity": "critical",
#       "rule": "cnw-aggr-if-down",
#       "severity": "critical",
#       "status": "",
#       "subject": "equipment",
#       "title": "",
#       "type": "operational"
#     }
#   }
# }
    def submit_faults(self, faults):
        self.log.info("JMWfaults submit_faults() processing %d faults", len(faults))
        for fault in faults:
            self.log.info("JMWfaults submit_faults() fault: %s", fault)
            # if isinstance(fault, dict):
            #     self.log.info("JMW fault is a dictionary")
            # else:
            #     self.log.info("JMW fault is NOT a dictionary")
            # if isinstance(fault, str):
            #     self.log.info("JMW fault is a str")
            # else:
            #     self.log.info("JMW fault is NOT a str")

            # for log_element in log_elements:
            #     payload = {}
            #     payload['ddtags'] = ",".join(tags)  # JMW same for faults?
            #     payload['message'] = log_element.get("MessageText")
            #     payload['timestamp'] = get_timestamp(datetime.datetime.fromisoformat(log_element.get("OccurredAt")))  # JMWTIMESTAMP
            #     payload['status'] = log_element.get("Category")
            #     payload['stage_name'] = name
            #     self.send_log(payload)  # JMWTUE try something like this

            payload = {}
            # JMWTAGS? payload['ddtags'] = ",".join(tags)  # JMW same for faults?
            # payload['ddsource'] = "cisco-aci-faults"  # JMW?

            # get created timestamp
            # last_transition = fault.get("faultInst", {}).get("attributes", {}).get("lastTransition")

            # JMW instead, do payload = fault["faultInst"]["attributes"] w/ try/except to log error if they dont exist as expected?
            faultinst = fault.get("faultInst", {})  # JMW dict
            attributes = faultinst.get("attributes", {})  # JMW dict

            # attributes is a dict
            # for each entry in the dict, add it to the payload
            # JMW map severity to status?
            # JMW should any other mappings be handled specially?
            # JMW are there any standard fields we should map/add?  descr-->message?  tags from config file?  ddsource, or is it already handled?  what else?
            #  standard attributes: host, timestamp, service, status (https://datadoghq.atlassian.net/wiki/spaces/LB/pages/2316567621/How+to+validate+a+logs+integration#Checklist)
            # JMWORIGWORKS for key, value in attributes.items():
                # JMW if value == "" then continue, or add it anyways?
                # JMW??? snmp traps don't have a message, just the JSON
                # JMWJMW if I do  this then it seems like we can only search on the message field
                # if key == "descr":  # JMW right?  should I also add it as descr?
                #    payload['message'] = value
                # JMWORIGWORKS payload[key] = value
                # JMWORIGWORKS if key == "lastTransition":
                    # JMWORIGWORKS payload['timestamp'] = get_timestamp(datetime.datetime.fromisoformat(attributes.get("lastTransition")))

            # JMWTRY
            # payload["message"] = attributes

            # JMWNEXTTRY
            payload = attributes

            # JMW move status to upgradeStatus
            # from https://pubhub.devnetcloud.com/media/apic-mim-ref-301/docs/MO-faultInst.html#overview
            # The upgrade status. This property is for internal use only.
            payload["upgradeStatus"] = payload.get("status", "")

            # JMW set status based on severity because status is a standard attribute
            #payload["status"] = payload.get("severity", "unknown")

            # JMW not 1-1 mapping for all?  explicitly map some values?
            # JMW critical, major, minor, warning, info, cleared
            # set payload "status" based on "severity"
            match payload.get("severity"):
                case "critical":
                    payload["status"] = "critical"
                case "major":
                    payload["status"] = "error"
                case "minor":
                    payload["status"] = "warning"
                case "warning":
                    payload["status"] = "warning"
                case "info":
                    payload["status"] = "info"
                case "cleared":
                    payload["status"] = "info"
                case _:
                    payload["status"] = "unknown"

            # JMW have code handle if lastTransition is missing just in case?
            payload["timestamp"] = get_timestamp(datetime.datetime.fromisoformat(attributes.get("lastTransition")))

            # payload['cause'] = attributes.get("cause")
            # payload['code'] = attributes.get("code")
            # payload['message'] = attributes.get("descr")
            # payload['severity'] = attributes.get("severity")
            # last_transition = attributes.get("lastTransition")  # JMW str
            # self.log.info("JMW last_transition: %s", last_transition)

            # self.log.info("JMW submit_faults() trying to get timstamp from created ", fault.get("faultInst", {}).get("attributes", {}).get("created"))
            # self.log.info("JMW submit_faults() trying to get timstamp from lastTransition ", fault.get("faultInst", {}).get("attributes", {}).get("lastTransition"))
            # payload['timestamp'] = get_timestamp(datetime.datetime.fromisoformat(fault.get("created")))

            # from base.py<check> comment: - timestamp: should be an integer or float representing the number of seconds since the Unix epoch
            # get current time in seconds
            # JMWWORKSpayload['timestamp'] = get_timestamp()
            # JMW
            # payload['timestamp'] = get_timestamp(datetime.datetime.fromisoformat(last_transition))

            # payload['status'] = fault.get("severity")
            # JMW other fields

            self.log.info("JMWfaults submit_faults() payload: %s", payload)
            self.send_log(payload)
