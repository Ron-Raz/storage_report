import math
import datetime
from KalturaClient import *
from KalturaClient.Plugins.Core import *

#
# the program creates a report of all VOD assets including the following columns:
# entryID, enterName, userId, createdAt, udpatedAt, lastPlayedAt, totalStorage, flavor1Size, flavor2Size, flavor3Size, etc.
#
# the program makes use of the following API calls:
#   https://developer.kaltura.com/api-docs/service/session/action/start
#   https://developer.kaltura.com/api-docs/service/media/action/list
#   https://developer.kaltura.com/api-docs/service/flavorAsset/action/list
#   https://developer.kaltura.com/api-docs/service/flavorParams/action/get
#

config = KalturaConfiguration()
config.serviceUrl = "https://www.kaltura.com/"
client = KalturaClient(config)
ks = client.session.start(
    "<admin_secret>",
    "<user>",
    KalturaSessionType.ADMIN,
    < partner_id >)
client.setKs(ks)


#
# loop on all media
#

def time2str(kalturaTime):
    ret = ''
    if kalturaTime:
        ret = datetime.datetime.fromtimestamp(kalturaTime).strftime('%m-%d-%Y')
    return ret


filterAsset = KalturaAssetFilter()
filterAsset.sizeGreaterThanOrEqual = 1
pagerAsset = KalturaFilterPager()
pagerMedia = KalturaFilterPager()
pagerMedia.pageSize = 100
filterMedia = KalturaMediaEntryFilter()
filterMedia.mediaTypeEqual = KalturaMediaType.VIDEO
filterMedia.createdAtGreaterThanOrEqual = 1136077261
delta = 10000000
stopDate = int(datetime.datetime.now().timestamp())
num = 0

flavorIds = {}
data = []

while filterMedia.createdAtGreaterThanOrEqual < stopDate:
    filterMedia.createdAtLessThanOrEqual = filterMedia.createdAtGreaterThanOrEqual+delta-1
    resultMedia = client.media.list(filterMedia, pagerMedia)
    print(time2str(filterMedia.createdAtGreaterThanOrEqual), resultMedia.totalCount)
    for pagerMedia.pageIndex in range(1, math.ceil(resultMedia.totalCount/pagerMedia.pageSize)+1):
        resultMedia = client.media.list(filterMedia, pagerMedia)
        for media in resultMedia.getObjects():
            obj = {'id': media.id, 'name': media.name, 'user': media.userId, 'createdAt': time2str(
                media.createdAt), 'updatedAt': time2str(media.updatedAt), 'lastPlayedAt': time2str(media.lastPlayedAt), 'flavors': {}, 'sumSizes': 0}
            num += 1
            filterAsset.entryIdEqual = media.id
            result = client.flavorAsset.list(filterAsset, pagerAsset)
            sumSizes = 0
            for flavor in result.getObjects():
                if not flavor.flavorParamsId in flavorIds:
                    flavorIds[flavor.flavorParamsId] = 0
                flavorIds[flavor.flavorParamsId] += 1
                obj['flavors'][flavor.flavorParamsId] = flavor.size
                sumSizes += flavor.size
            obj['sumSizes'] = str(sumSizes)
            data.append(obj)
    filterMedia.createdAtGreaterThanOrEqual += delta

#
# output the report
#

reportFile = open('report.tsv', 'w')
cols = ''
for flavor in flavorIds:
    result = client.flavorParams.get(flavor)
    cols += '\t'+result.name+' ['+str(flavor)+']'
reportFile.write('\t'.join(['ENTRY_ID', 'ENTRY_NAME', 'USER_ID', 'CREATED_AT',
                            'UPDATED_AT', 'LAST_PLAYED_AT', 'TOTAL_STORAGE'])+cols+'\n')

for row in data:
    cols = ''
    for flavor in flavorIds:
        if flavor in row['flavors']:
            cols += '\t'+str(row['flavors'][flavor])
        else:
            cols += '\t0'
    reportFile.write('\t'.join([row['id'], row['name'], row['user'], row['createdAt'],
                                row['updatedAt'], row['lastPlayedAt'], row['sumSizes']])+cols+'\n')

reportFile.close()
