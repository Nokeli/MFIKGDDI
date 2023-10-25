import numpy as np

f = open('raw_data/kegg/entity2id.txt', 'r')
drugbank_id_kegg = []
drugbank_id_kegg_dict = dict()
flag = 0
for line in f.readlines():
    flag = flag + 1
    row = line.strip().split("\t")

    if "drugbank:" in str(row[0]):
        split_result = row[0].split(":")
        #print(row[0].split(":"))
        id = split_result[2][0:7]
        drugbank_id_kegg.append([id,row[1]])
        drugbank_id_kegg_dict[row[1]] = id

    if "drugbank/" in str(row[0]):
        #print(row[0])
        split_result = row[0].split("/")
        id = split_result[4][0:7]
        drugbank_id_kegg.append([id, row[1]])
        drugbank_id_kegg_dict[row[1]] = id


#print(drugbank_id_kegg)
print(len(np.unique(np.array(drugbank_id_kegg)[:,0])))
np.save("raw_data/kegg/drugid",drugbank_id_kegg)
#finally there are 1463 unique drugs in kegg dataset'''
print(drugbank_id_kegg_dict)