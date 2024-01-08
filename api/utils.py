import tensorflow as tf

def load_model():
    model = tf.keras.models.load_model("../model/modelVip.h5")
    return model