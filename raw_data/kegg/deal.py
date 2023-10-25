import pandas as pd
import numpy as np
from yoctol_utils.hash import consistent_hash
def hash_seq(sequence, max_index):
    #print(sequence)
    return np.array([consistent_hash(word) % max_index + 1 for word in sequence])
#获取approved_drug 编号
approved = open("approved_example.txt",'r')
approved_lines = approved.readlines()
drug_set = set()
for i in approved_lines:
    line = i.strip().split('\t')
    drug_set.add(line[0])
print(len(drug_set))
#
entity_file = open("entity2id.txt",'r')
entity_lines = entity_file.readlines()
entity_dict = dict()
flag = 1
for en in entity_lines:
    if flag == 1 :
        flag = 0
        continue
    en_line = en.strip().split('\t')
    entity_dict[en_line[1]] = en_line[0]
k = 0
#序号到实体名字
drug_id = dict()
for i in drug_set:
    if 'kegg:' in entity_dict[i]:
        k = k+1
        entity_id = entity_dict[i][1:-1]
        entity_id = entity_id.split('kegg:')
        drug_id[i] = entity_id[1]
#print(drug_id)
#处理drugbank文件
df = pd.read_csv('structure_links.csv',keep_default_na = False)
length = df.shape[0]
# df.iloc[:,9]
# df.iloc[:,6]
kegg_drug_id_to_SMILE = dict()
for i in range(length):
    if df.iloc[i,6] is not None and df.iloc[i,9] is not None and df.iloc[i,6] !='':
        kegg_drug_id_to_SMILE[df.iloc[i,9]] = df.iloc[i,6]
#print(kegg_drug_id_to_SMILE)
#print(kegg_drug_id_to_SMILE.keys())
k = 0
kegg_drug_SMILE = dict()
for v in drug_id.keys():
    if drug_id[v] in kegg_drug_id_to_SMILE.keys():
        kegg_drug_SMILE[v] = kegg_drug_id_to_SMILE[drug_id[v]]
print(len(kegg_drug_SMILE))
drug_list = []
with open('smiles.txt','w') as f:
    for i in sorted(kegg_drug_SMILE):
        drug_list.append((i,kegg_drug_SMILE[i]))
        f.write(kegg_drug_SMILE[i]+'\n')
#print(drug_list)

# f = open('entity2id.txt', 'r')
# drugbank_id_kegg = []
# drugbank_id_kegg_dict = dict()
# flag = 0
# for line in f.readlines():
#     flag = flag + 1
#     row = line.strip().split("\t")

#     if "drugbank:" in str(row[0]):
#         split_result = row[0].split(":")
#         #print(row[0].split(":"))
#         id = split_result[2][0:7]
#         drugbank_id_kegg.append([id,row[1]])
#         drugbank_id_kegg_dict[row[1]] = id

#     if "drugbank/" in str(row[0]):
#         #print(row[0])
#         split_result = row[0].split("/")
#         id = split_result[4][0:7]
#         drugbank_id_kegg.append([id, row[1]])
#         drugbank_id_kegg_dict[row[1]] = id


# #print(drugbank_id_kegg)
# # print(len(np.unique(np.array(drugbank_id_kegg)[:,0])))
# # np.save("raw_data/kegg/drugid",drugbank_id_kegg)
# #finally there are 1463 unique drugs in kegg dataset'''
# print(drugbank_id_kegg_dict)
# n = 0
# for key in drug_id.keys():
#     if key in drugbank_id_kegg_dict.keys():
#         n = n +1
# print(n)
#生成能生成分子图的表征
smiles = []
hashes = []
mole_embedding = []
SELF_embedding = []
mole_embedding_TrueorFalse = np.load('mol_parsed.npy')
mole_embedding_vec = np.load('mol_emb.npy')
mole_SELF_embedding_vec = np.load('kegg_SELF_embedding.npy')
drug_new_list = []
n = 0
for i in range(len(mole_embedding_TrueorFalse)):
    if mole_embedding_TrueorFalse[i] == True:
        #print(mole_embedding_TrueorFalse[i])
        drug_new_list.append(drug_list[i])
print(len(drug_new_list))
f = open("entity2id.txt",'r')
flag = 1
for line in f.readlines():
    if flag==1:
        flag=0
        continue
    row = line.strip().split("\t")
    drugid = str(row[1])
    itemindex = [index for index in range(len(drug_new_list)) if drug_new_list[index][0] == drugid]
    if len(itemindex) == 0:
        smiles.append([" "])
        mole_vec = np.zeros(300)
        SELF_vec = np.zeros(768)
#        hash_vec = np.zeros(512)
#        hashes.append(hash_vec)
        mole_embedding.append(mole_vec)
        SELF_embedding.append(SELF_vec)
    else:
        print(itemindex[0])
        strings = []
        for chars in range(0,len(drug_new_list[itemindex[0]][1])):
            strings.append(drug_new_list[itemindex[0]][1][chars])
        #print(len(strings))
#        hashes.append(hash_seq(strings,512))
        smiles.append(strings)
        mole_embedding.append(mole_embedding_vec[itemindex[0]])
        SELF_embedding.append(mole_SELF_embedding_vec[itemindex[0]])
#hashes = np.array(hashes)
mole_embedding = np.array(mole_embedding)
SELF_embedding = np.array(SELF_embedding)
#np.save("kegg_2_drugbank_smile_hash", hashes)
np.save("kegg_2_drugbank_mole_embedding",mole_embedding)
np.save("kegg_2_drugbank_SELF_embedding",SELF_embedding)

# hashes = np.load("kegg_2_drugbank_smile_hash.npy",allow_pickle=True)
# new_hash = []
# for i in hashes:
#     if len(i) == 512:
#         print("yes")
#         new_hash.append(i)
#     else:
#         print(i)
#         print(len(i))
#         padding = np.zeros(512-len(i))
#         new_hashes = np.concatenate((padding,i),axis=0)
#         new_hash.append(new_hashes)

# new_hash = np.array(new_hash)
# print(np.array(new_hash).shape)
# print(new_hash.reshape(len(hashes),512))
# np.save("kegg_2_drugbank_smile_hash", new_hash)



