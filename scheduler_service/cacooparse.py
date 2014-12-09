import requests
from lxml import etree
import json

def getCacooDesignJSON():
    # api key for cacoo is hardcoded (Henry's personal account)
    apikey_str = "?apiKey=vVHejHcoUfFrdsViTj0e"
    #http://docs.python-requests.org/en/latest/
    r = requests.get("https://cacoo.com/api/v1/diagrams.json" + apikey_str)
    rj = r.json()
    diagId = rj['result'][0]['diagramId']
    print diagId
    contentUrl = "https://cacoo.com/api/v1/diagrams/" + diagId + "/contents.xml" + apikey_str
    contentUIDUrl = contentUrl + "&returnValues=uid,textStyle"
    r1 = requests.get(contentUIDUrl)
    r1t = r1.text
    # xml from cacoo has unicode encoding explicitly specified at the top of the
    # xml file.  This presents an issue for lxml.  See
    # http://lxml.de/dev/FAQ.html#why-can-t-lxml-parse-my-xml-from-unicode-strings
    # http://lxml.de/parsing.html#python-unicode-strings
    # for a temporary solution use suggestion described in
    # http://stackoverflow.com/questions/3402520/is-there-a-way-to-force-lxml-to-parse-unicode-strings-that-specify-an-encoding-i
    utf8_parser = etree.XMLParser(encoding='utf-8')
    r1t_uencode = r1t.encode('utf-8')
    root = etree.fromstring(r1t_uencode, parser=utf8_parser)
    #print etree.tostring(root, pretty_print=True)
    #print "num of sheets="+str(len(root))
    # for break: look definition in Learning Python, p.254
    for sheet in root:
        if sheet.attrib['name'].lower() == 'design':
            print "Design sheet found"
            design_sheet = sheet
            break
    else:
        design_sheet = None
    # ref for breaking out of nexted loops
    # http://stackoverflow.com/questions/653509/breaking-out-of-nested-loops
    stencil_id_list = []
    if (design_sheet):
        for elem in design_sheet:
            print etree.tostring(elem, pretty_print=True)
            #stencil_id_list.append(int(group_stencil_id_str))
            # detect cloud cacoo stencil object
            if elem.tag == 'group':
                # if we have a group, find stencil id.
                # if it is a recognized stencil id, add to list
                sid = int(elem.get('attr-stencil-id', -1))
                if sid > -1:
                    stencil_id_list.append(sid)
                    if sid == 16:
                        # if stencil id is 16, we have a 'cloud' stencil
                        for elem2 in elem:
                            if elem2.tag == 'text':
                                for elem3 in elem2:
                                    if elem3.tag == 'textStyle':
                                        cloudName = elem3.text
                                        break
                                else:
                                    continue
                                break
                        else:
                            continue
                        break
        else:
            cloudName = None # if all loops complete w.out break
    else:
        cloudName = None # if design_sheet does not exist

    if cloudName:
        print "cloudName =", cloudName

    #print r1.text
    '''
    sheet2 = root[2]
    num_elements = len(sheet2)
    stencil_id_list = []
    for elem in sheet2:
        #print elem.tag
        #print etree.tostring(elem, pretty_print=True)
        if elem.tag == 'group':
            group_stencil_id_str = elem.attrib['attr-stencil-id']
            stencil_id_list.append(int(group_stencil_id_str))
            for elem2 in elem:
                print elem2.tag, elem2.text
                if elem2.tag == 'text':
                    for elem3 in elem2:
                        print "text element nodes", elem3.tag, elem3.text
    '''
    a = json.dumps({"stencil_id":stencil_id_list})
    return a
