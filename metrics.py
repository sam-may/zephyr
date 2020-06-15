import tensorflow as tf
import tensorflow.keras as keras

def weighted_crossentropy(alpha):
    def calc_weighted_crossentropy(y_true, y_pred):
        y_pred = keras.backend.clip(y_pred, keras.backend.epsilon(), 1 - keras.backend.epsilon()) # to prevent nan's in loss
    
        positive_term = alpha * (-y_true * keras.backend.log(y_pred)) # naively set alpha = sum(negative instances) / sum(positive instances)
        negative_term = -(1 - y_true) * keras.backend.log(1 - y_pred)
        return keras.backend.mean(positive_term + negative_term)

    return calc_weighted_crossentropy

def dice_loss(y_true, y_pred):
    num_pos   = 2 * tf.reduce_sum(y_true * y_pred)
    denom_pos = tf.reduce_sum(y_true + y_pred)

    num_neg   = 2 * tf.reduce_sum((1-y_true) * (1-y_pred))
    denom_neg = tf.reduce_sum((1-y_true) + (1-y_pred))

    return 1 - ((0.5 * num_pos) / denom_pos) - ((0.5 * num_neg) / denom_neg)
