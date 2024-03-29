import tensorflow as tf
import tensorflow.keras as keras

def weighted_crossentropy(bce_alpha, **kwargs):
    def calc_weighted_crossentropy(y_true, y_pred):
        """
        Calculate binary cross entropy with 
        weight alpha applied to positive cases
        """ 
        y_pred = keras.backend.clip(
            y_pred, 
            keras.backend.epsilon(), 
            1-keras.backend.epsilon()
        ) # to prevent nan's in loss
        # Naively set alpha = sum(negative instances)/sum(positive instances)
        positive_term = bce_alpha*(-y_true*keras.backend.log(y_pred)) 
        negative_term = -(1-y_true)*keras.backend.log(1-y_pred)

        return keras.backend.mean(positive_term + negative_term)

    return calc_weighted_crossentropy

def dice_loss(dice_smooth, **kwargs):
    def calc_dice_loss(y_true, y_pred):
        """
        Calculate dice loss = 2 * (smooth + intersection) / (smooth + size(truth) + size(pred))
        smooth parameter helps with convergence when the numerator/denominator is very small
        """
        numerator = 2 * (dice_smooth + tf.reduce_sum(y_true * y_pred))
        denominator = dice_smooth + tf.reduce_sum(y_true + y_pred)

        return 1 - (numerator / denominator)

    return calc_dice_loss

