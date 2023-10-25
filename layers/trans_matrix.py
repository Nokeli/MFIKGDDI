from keras.engine.topology import Layer
from keras import backend as K

class Trans_Matrix(Layer):
    def __init__(self,entity_dim = 32,output_dim = 32,initializer='glorot_normal', regularizer=None,
    **kwargs):
        super(Trans_Matrix,self).__init__(**kwargs)
        self.entity_dim = entity_dim
        self.initializer = initializer
        self.regularizer = regularizer
        self.output_dim = output_dim
    def build(self,input_shape):
        mole_embedding_dim = input_shape[-1]
        enti_dim = self.entity_dim
        self.w_h = self.add_weight(name = self.name+'_wh',shape=(mole_embedding_dim,enti_dim),
                initializer = self.initializer,regularizer = self.regularizer)
        self.b_h = self.add_weight(name = self.name+'_wh',shape=(self.entity_dim,enti_dim),
                initializer = self.initializer,regularizer = self.regularizer)
        super(Trans_Matrix,self).build(input_shape)
    def call(self,inputs,**kwargs):
        mole_embed = K.dot(inputs,self.w_h)
        #mole_embed = mole_embed + self.b_h
        print("print trans 300 to 32")
        print(mole_embed.shape)
        return mole_embed
    def compute_output_shape(self,input_shape):
        return (input_shape[0],self.output_dim)