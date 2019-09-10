# ACI-Library
This is a basic ACI python library to be used to create automation tools.  

It can also be used to run on-the-fly queries and make posts.

for example, to pull the configuration of an EPG, modify it and post the change, you might do this:

>>> from fabric import Fabric
>>> lab = Fabric('lab.company.com')
>>> lab.login()
Username: davis
Password:
>>> data = lab.qr('uni/tn-BU1/ap-PROD/epg-TEST1', include='config-only').data
>>> data.print()
{
  "totalCount": "1",
  "imdata": [
    {
      "fvAEPg": {
        "attributes": {
          "annotation": "",
          "descr": "",
          "dn": "uni/tn-BU1/ap-PROD/epg-TEST1",
          "exceptionTag": "",
          "floodOnEncap": "disabled",
          "fwdCtrl": "",
          "isAttrBasedEPg": "no",
          "matchT": "AtleastOne",
          "name": "TEST1",
          "nameAlias": "",
          "pcEnfPref": "unenforced",
          "prefGrMemb": "exclude",
          "prio": "unspecified"
        }
      }
    }
  ]
}
>>> data.imdata[0]["fvAEPg"]["attributes"]["nameAlias"] = "TEST-EPG-1"
>>> data.imdata[0]["fvAEPg"]["attributes"]["descr"] = "A Test Network"
>>> lab.post(data.json)
200
>>> lab.qr("uni/tn-BU1/ap-PROD/epg-TEST1", include="config-only").print(0)
{
  "totalCount": "1",
  "imdata": [
    {
      "fvAEPg": {
        "attributes": {
          "annotation": "",
          "descr": "A Test Network",
          "dn": "uni/tn-BU1/ap-PROD/epg-TEST1",
          "exceptionTag": "",
          "floodOnEncap": "disabled",
          "fwdCtrl": "",
          "isAttrBasedEPg": "no",
          "matchT": "AtleastOne",
          "name": "TEST1",
          "nameAlias": "TEST-EPG-1",
          "pcEnfPref": "unenforced",
          "prefGrMemb": "exclude",
          "prio": "unspecified"
        }
      }
    }
  ]
}
