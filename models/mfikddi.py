# -*- coding: utf-8 -*-
# @Time    : 2020-10-22 15:53
# @Author  : xiaorui su
# @Email   :  suxiaorui19@mails.ucas.edu.cn
# @File    : ddkg.py
# @Software : PyCharm


from keras.layers import *
from keras.regularizers import l2
from keras.models import Model
from keras import backend as K  # use computable function
from sklearn.metrics import roc_auc_score, accuracy_score, f1_score, precision_recall_curve
import sklearn.metrics as m
from layers import Aggregator,MultiAttention,Trans_Matrix
from callbacks import KGCNMetric
import tensorflow as tf
from models.base_model import BaseModel
from keras.layers import Input,LSTM,Dense
from yoctol_utils.hash import consistent_hash




class MFIKDDI(BaseModel):

    def __init__(self, config):
        super(MFIKDDI, self).__init__(config)

    def build(self):

        input_drug_one = Input(
            # drug_one id
            shape=(1,), name='input_drug_one',dtype='int64')
        input_drug_two = Input(
            # drug_two_id
            shape=(1,), name='input_drug_two', dtype='int64')

        #embedding container
        entity_embedding = Embedding(input_dim=self.config.entity_vocab_size,
                                     output_dim=self.config.embed_dim,
                                     embeddings_initializer='glorot_normal',
                                     embeddings_regularizer=l2(
                                         self.config.l2_weight),
                                     name='entity_embedding')
        # relation are supposed to feet into a encoder-decoder layer
        relation_embedding = Embedding(input_dim=self.config.relation_vocab_size,
                                       output_dim=self.config.embed_dim,
                                       embeddings_initializer='glorot_normal',
                                       embeddings_regularizer=l2(
                                           self.config.l2_weight),
                                       name='relation_embedding')
        drug_one_embedding = Embedding(input_dim=self.config.drug_vocab_size,
                                       output_dim=self.config.embed_dim,
                                       embeddings_initializer='glorot_normal',
                                       embeddings_regularizer=l2(
                                           self.config.l2_weight),
                                       name='user_embedding')


        # drug encoder-decoder embedding results
        #match id to smiles
        #original hash embedding
        print("smile")
        drug_embedding_one = drug_one_embedding(input_drug_one)
        #原始代码****
        drug_one_mole_embedding = Lambda(lambda x: self.get_mole_embedding(x),name='get_drug_mole_embedding')(input_drug_one)
        drug_one_self_embedding = Lambda(lambda x: self.get_SELF_embedding(x),name='get_drug_self_embedding')(input_drug_one)
        drug_one_combine_embedding = Lambda(lambda x: self.combine(x[0],x[1]),name='combine_embedding')([drug_one_self_embedding,drug_one_mole_embedding])
        drug_one_add_embedding = Lambda(lambda x: self.add(x[0],x[1]),name='add_embedding')([drug_one_combine_embedding,drug_embedding_one])
        #原始代码****
        #print(drug_embedding_one)
        ##using layer
        #drug_one_embedding = self.drug_embedding(self.get_hash(input_drug_one))
        #drug_hash = Lambda(lambda x: self.get_hash(x),name="get_drug_smile_hash")(input_drug_one) #batch_size,8,64
        #drug_one_embedding = Lambda(lambda x: self.drug_embedding(x),name="get_drug_embedding")(drug_hash)
        #加入mole向量
        #print(drug_one_embedding)
        #消融实验-删掉序列特征***
        #drug_one_mole_embedding = Lambda(lambda x: self.get_mole_embedding(x),name='get_drug_mole_embedding')(input_drug_one)
        #*****
        # #print('drug_one_mole_embedding')
        # #print(drug_one_mole_embedding)


        #get list
        receptive_list_drug_one = Lambda(lambda x: self.get_receptive_field(x),
                                         name='receptive_filed_drug_one')(input_drug_one)
        neineigh_ent_list_drug_one = receptive_list_drug_one[:self.config.n_depth + 1]
        neigh_rel_list_drug_one = receptive_list_drug_one[self.config.n_depth + 1:]

        #get embeded
        neigh_ent_embed_list_drug_one = [entity_embedding(
            neigh_ent) for neigh_ent in neineigh_ent_list_drug_one]
        neigh_rel_embed_list_drug_one = [relation_embedding(
            neigh_rel) for neigh_rel in neigh_rel_list_drug_one]
        neighbor_embedding = Lambda(lambda x: self.get_neighbor_info_attention(x[0], x[1], x[2]),
                                    name='neighbor_embedding_drug_one')

        for depth in range(self.config.n_depth):
            aggregator = Aggregator[self.config.aggregator_type](
                activation='tanh' if depth == self.config.n_depth-1 else 'relu',
                regularizer=l2(self.config.l2_weight),
                name=f'aggregator_{depth+1}_drug_one'
            )

            next_neigh_ent_embed_list_drug_one = []
            for hop in range(self.config.n_depth-depth):
                #消融实验-去除序列信息
                # neighbor_embed = neighbor_embedding([drug_one_mole_embedding, neigh_rel_embed_list_drug_one[hop],
                #                                       neigh_ent_embed_list_drug_one[hop + 1]])
                #*****
                neighbor_embed = neighbor_embedding([drug_one_combine_embedding, neigh_rel_embed_list_drug_one[hop],
                                                    neigh_ent_embed_list_drug_one[hop + 1]])
                next_entity_embed = aggregator(
                    [neigh_ent_embed_list_drug_one[hop], neighbor_embed])
                next_neigh_ent_embed_list_drug_one.append(next_entity_embed)
            neigh_ent_embed_list_drug_one = next_neigh_ent_embed_list_drug_one


        ###for second drug
        drug_embedding_two = drug_one_embedding(input_drug_two)
        #drug_embedding = self.drug_embedding(self.get_hash(input_drug_two))
        #drug_hash = Lambda(lambda x:self.get_hash(x),name='get_drug2_smile_hash')(input_drug_two)#?,8,64
        #drug_embedding = Lambda(lambda x: self.drug_embedding(x), name="get_drug2_embedding")(drug_hash)
        #原始代码***
        drug_two_mole_embedding = Lambda(lambda x: self.get_mole_embedding(x), name='get_drug_mole_embedding2')(input_drug_two)
        drug_two_self_embedding = Lambda(lambda x: self.get_SELF_embedding(x),name='get_drug_self_embedding2')(input_drug_two)
        drug_two_combine_embedding = Lambda(lambda x: self.combine(x[0], x[1]), name='combine_embedding2')([drug_two_self_embedding, drug_two_mole_embedding])
        drug_two_add_embedding = Lambda(lambda x: self.add(x[0],x[1]),name='add_embedding2')([drug_two_combine_embedding,drug_embedding_two])
        #****
        #消融实验-去除序列信息：
        drug_two_mole_embedding = Lambda(lambda x: self.get_mole_embedding(x), name='get_drug_mole_embedding2')(input_drug_two)
        #***
        #print(drug_tow_combine_embedding)

        # get list
        receptive_list_drug = Lambda(lambda x: self.get_receptive_field(x),
                                         name='receptive_filed_drug_two')(input_drug_two)
        neineigh_ent_list_drug = receptive_list_drug[:self.config.n_depth + 1]
        neigh_rel_list_drug = receptive_list_drug[self.config.n_depth + 1:]

        # get embeded
        neigh_ent_embed_list_drug = [entity_embedding(
            neigh_ent) for neigh_ent in neineigh_ent_list_drug]
        neigh_rel_embed_list_drug = [relation_embedding(
            neigh_rel) for neigh_rel in neigh_rel_list_drug]
        neighbor_embedding = Lambda(lambda x: self.get_neighbor_info_attention(x[0], x[1], x[2]),
                                    name='neighbor_embedding_drug_two')

        for depth in range(self.config.n_depth):
            aggregator = Aggregator[self.config.aggregator_type](
                activation='tanh' if depth == self.config.n_depth - 1 else 'relu',
                regularizer=l2(self.config.l2_weight),
                name=f'aggregator_{depth + 1}_drug'
            )

            next_neigh_ent_embed_list_drug = []
            for hop in range(self.config.n_depth - depth):
                ###消融实验-去除序列信息
                # neighbor_embed = neighbor_embedding([drug_two_mole_embedding, neigh_rel_embed_list_drug[hop],
                #                                      neigh_ent_embed_list_drug[hop + 1]])
                #*******
                neighbor_embed = neighbor_embedding([drug_two_combine_embedding, neigh_rel_embed_list_drug[hop],
                                                    neigh_ent_embed_list_drug[hop + 1]])
                next_entity_embed = aggregator(
                    [neigh_ent_embed_list_drug[hop], neighbor_embed])
                next_neigh_ent_embed_list_drug.append(next_entity_embed)
            neigh_ent_embed_list_drug = next_neigh_ent_embed_list_drug


        ##model
        result_one = Lambda(lambda x: self.res_com(x[0],x[1]),name='res_com1')([drug_one_add_embedding,neigh_ent_embed_list_drug_one[0]])
        result_two = Lambda(lambda x: self.res_com(x[0],x[1]),name='res_com2')([drug_two_add_embedding,neigh_ent_embed_list_drug[0]])
        #消融实验-去除序列信息
        # result_one = Lambda(lambda x: self.res_com(x[0],x[1]),name='res_com1')([drug_one_mole_embedding,neigh_ent_embed_list_drug_one[0]])
        # result_two = Lambda(lambda x: self.res_com(x[0],x[1]),name='res_com2')([drug_two_mole_embedding,neigh_ent_embed_list_drug[0]])
        #****
        drug1_squeeze_embed = Lambda(lambda x: K.squeeze(
           x, axis=1))(result_one)
        # drug1_squeeze_embed = Lambda(lambda x: K.squeeze(
        #     x, axis=1))(neigh_ent_embed_list_drug_one[0])
        drug2_squeeze_embed = Lambda(lambda x: K.squeeze(
           x, axis=1))(result_two)
        # drug2_squeeze_embed = Lambda(lambda x: K.squeeze(
        #     x, axis=1))(neigh_ent_embed_list_drug[0])
        drug_drug_score = Lambda(
            lambda x: K.sigmoid(K.sum(x[0] * x[1], axis=-1, keepdims=True))
        )([drug1_squeeze_embed, drug2_squeeze_embed])

        model = Model([input_drug_one, input_drug_two], drug_drug_score)
        model.compile(optimizer=self.config.optimizer,
                      loss='binary_crossentropy', metrics=['acc'])
        return model

    def get_hash(self, drugid):

        ##load smile matrix

        drug_smile_matrix =  K.variable(
            self.config.smile_hash, name='smile_hash')
        print(drug_smile_matrix)
        drug_smile_entity = K.gather(drug_smile_matrix, K.cast(
                drugid, dtype='int64')) #get drug's hash
        print(drug_smile_entity)

        drug_hash_embed = K.reshape(drug_smile_entity, (-1,int(self.config.timestep),int(self.config.latent_dim/self.config.timestep),))#?,8,64

        return drug_hash_embed

    def get_mole_embedding(self,drugid):
        drug_mole_matrix = K.variable(self.config.mole_embedding,name='mole_embedding')
        print(drug_mole_matrix)
        drug_mole_embedding_entity = K.gather(drug_mole_matrix,K.cast(drugid,dtype='int64'))
        print(drug_mole_embedding_entity)
        #drug_hash_embedding = K.reshape(drug_mole_embedding_entity,(-1,1,300))
        drug_mole_embedding = Dense(self.config.embed_dim,activation='sigmoid')(drug_mole_embedding_entity)
        # trans_matrix = Trans_Matrix(regularizer=l2(self.config.l2_weight),
        #                           name='Trans_layer')
        # print('trans_matrix')
        # drug_mole_embedding = trans_matrix(drug_mole_embedding_entity)
        # print(drug_mole_embedding)
        return drug_mole_embedding
    def get_SELF_embedding(self,drugid):

        drug_SELF_matrix = K.variable(self.config.self_embedding,name='self_embedding')
        print(drug_SELF_matrix)
        drug_self_embedding_entity = K.gather(drug_SELF_matrix,K.cast(drugid,dtype='int64'))
        print(drug_self_embedding_entity)
        #drug_hash_embedding = K.reshape(drug_mole_embedding_entity,(-1,1,300))
        drug_self_embedding = Dense(self.config.embed_dim,activation='sigmoid')(drug_self_embedding_entity)
        return drug_self_embedding


    def combine(self,drug_smiles_embedding,drug_mole_embedding):
        combine_embedding = Multiply()([drug_smiles_embedding,drug_mole_embedding])
        return combine_embedding
    def add(self,drug_mole_embedding,drug_self_embedding):
        add_embedding = Add()([drug_mole_embedding,drug_self_embedding])
        return add_embedding
    
    def res_com(self,drug_combine_embedding,drug_result):
        result = Add()([drug_combine_embedding,drug_result])
        return result


    def drug_embedding(self, input_drug):

        ##encoder-decoder
        drug_embed = input_drug
        print(drug_embed)
        encoder = LSTM(self.config.latent_dim, return_state=True)  #64->512
        encoder_outputs, state_h, state_c = encoder(drug_embed)
        print("encoder_outputs")
        print(encoder_outputs) #1,512
        encoder_states = [state_h, state_c]
        # We set up our decoder to return full output sequences,
        # and to return internal states as well. We don't use the
        # return states in the training model, but we will use them in inference.
        encoder_outputs = K.reshape(encoder_outputs,(-1,1,self.config.latent_dim))
        decoder_lstm = LSTM(self.config.latent_dim, return_sequences=True, return_state=True)
        decoder_outputs, _, _ = decoder_lstm(encoder_outputs,
                                             initial_state=encoder_states)
        decoder_outputs = Dense(self.config.embed_dim, activation='softmax')(decoder_outputs)  # drug_emebdding_end

        print("decoder_outputs")
        print(decoder_outputs)

        return decoder_outputs


    def get_receptive_field(self, entity):
        """Calculate receptive field for entity using adjacent matrix

        :param entity: a tensor shaped [batch_size, 1]
        :return: a list of tensor: [[batch_size, 1], [batch_size, neighbor_sample_size],
                                   [batch_size, neighbor_sample_size**2], ...]
        """
        neigh_ent_list = [entity]
        neigh_rel_list = []
        adj_entity_matrix = K.variable(
            self.config.adj_entity, name='adj_entity', dtype='int64')
        adj_relation_matrix = K.variable(self.config.adj_relation, name='adj_relation',
                                         dtype='int64')
        n_neighbor = K.shape(adj_entity_matrix)[1]

        for i in range(self.config.n_depth):
            new_neigh_ent = K.gather(adj_entity_matrix, K.cast(
                neigh_ent_list[-1], dtype='int64'))  # cast function used to transform data type
            new_neigh_rel = K.gather(adj_relation_matrix, K.cast(
                neigh_ent_list[-1], dtype='int64'))
            neigh_ent_list.append(
                K.reshape(new_neigh_ent, (-1, n_neighbor ** (i + 1))))
            neigh_rel_list.append(
                K.reshape(new_neigh_rel, (-1, n_neighbor ** (i + 1))))

        return neigh_ent_list + neigh_rel_list

    def get_neighbor_info(self, drug, rel, ent):
        """Get neighbor representation.

        :param user: a tensor shaped [batch_size, 1, embed_dim]
        :param rel: a tensor shaped [batch_size, neighbor_size ** hop, embed_dim]
        :param ent: a tensor shaped [batch_size, neighbor_size ** hop, embed_dim]
        :return: a tensor shaped [batch_size, neighbor_size ** (hop -1), embed_dim]
        """
        # [batch_size, neighbor_size ** hop, 1] drug-entity score
        drug_rel_score = K.sum(drug * rel, axis=-1, keepdims=True)

        # [batch_size, neighbor_size ** hop, embed_dim]
        ###类似于attention机制
        weighted_ent = drug_rel_score * ent

        # [batch_size, neighbor_size ** (hop-1), neighbor_size, embed_dim]
        weighted_ent = K.reshape(weighted_ent,
                                 (K.shape(weighted_ent)[0], -1,
                                  self.config.neighbor_sample_size, self.config.embed_dim))

        neighbor_embed = K.sum(weighted_ent, axis=2)
        return neighbor_embed
    def get_neighbor_info_attention(self,drug,rel,ent):
        """Get neighbor representation.

        :param user: a tensor shaped [batch_size, 1, embed_dim]
        :param rel: a tensor shaped [batch_size, neighbor_size ** hop, embed_dim]
        :param ent: a tensor shaped [batch_size, neighbor_size ** hop, embed_dim]
        :return: a tensor shaped [batch_size, neighbor_size ** (hop -1), embed_dim]
        """
        # [batch_size, neighbor_size ** hop, 1] drug-entity score
        mulAtten = MultiAttention(activation='tanh', regularizer=l2(self.config.l2_weight),
                                  name='multi_attention_layer')
        eighted_ent = mulAtten([drug, rel, ent])
        #print(attention_weight) 
        #eighted_ent = attention_weight * ent

        # [batch_size, neighbor_size ** hop, embed_dim]

        eighted_ent = K.reshape(eighted_ent,
                                (K.shape(eighted_ent)[0], -1, self.config.neighbor_sample_size, self.config.embed_dim))

        # [batch_size, neighbor_size ** (hop-1), neighbor_size, embed_dim]
        result_embed = K.sum(eighted_ent, axis=2)
        return result_embed


    def add_metrics(self, x_train, y_train, x_valid, y_valid):
        self.callbacks.append(KGCNMetric(x_train, y_train, x_valid, y_valid,
                                         self.config.aggregator_type, self.config.dataset, self.config.K_Fold))

    def fit(self, x_train, y_train, x_valid, y_valid):
        self.callbacks = []
        self.add_metrics(x_train, y_train, x_valid, y_valid)
        self.init_callbacks()

        print('Logging Info - Start training...')
        self.model.fit(x=x_train, y=y_train, batch_size=self.config.batch_size,
                       epochs=self.config.n_epoch, validation_data=(
                           x_valid, y_valid),
                       callbacks=self.callbacks)
        print('Logging Info - training end...')

    def predict(self, x):
        return self.model.predict(x).flatten()

    def score(self, x, y, threshold=0.5):
        y_true = y.flatten()
        y_pred = self.model.predict(x).flatten()
        auc = roc_auc_score(y_true=y_true, y_score=y_pred)
        from sklearn.metrics import roc_curve
        fpr,tpr,thr = roc_curve(y_true=y_true, y_score=y_pred)
        p, r, t = precision_recall_curve(y_true=y_true, probas_pred=y_pred)
        aupr = m.auc(r, p)
        y_pred = [1 if prob >= threshold else 0 for prob in y_pred]
        acc = accuracy_score(y_true=y_true, y_pred=y_pred)
        f1 = f1_score(y_true=y_true, y_pred=y_pred)

        return auc, acc, f1, aupr, fpr.tolist(), tpr.tolist()
