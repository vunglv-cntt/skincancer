import tensorflow as tf

def load_model():
    model = tf.keras.models.load_model("../model/modelchuan.h5")
    return model