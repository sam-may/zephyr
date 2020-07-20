import tensorflow as tf
import tensorflow.keras as keras

def weighted_crossentropy(alpha):
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
        positive_term = alpha*(-y_true*keras.backend.log(y_pred)) 
        negative_term = -(1-y_true)*keras.backend.log(1-y_pred)

        return keras.backend.mean(positive_term + negative_term)

    return calc_weighted_crossentropy

def dice_loss(smooth):
    def calc_dice_loss(y_true, y_pred):
        """
        Calculate dice loss = 2 * (smooth + intersection) / (smooth + size(truth) + size(pred))
        smooth parameter helps with convergence when the numerator/denominator is very small
        """
        numerator = 2 * (smooth + tf.reduce_sum(y_true * y_pred))
        denominator = smooth + tf.reduce_sum(y_true + y_pred)

        return 1 - (numerator / denominator)

    return calc_dice_loss

loss_dictionary = {
    "weighted_crossentropy" : {
        "function" : weighted_crossentropy,
        "args" : ["bce_alpha"]
    },
    "dice_loss" : {
        "function" : dice_loss,
        "args" : ["dice_smooth"]
    }
}

def choose_loss(loss, loss_hyperparams):
    if loss not in loss_dictionary.keys():
        raise ValueError("[loss_functions.py] Loss function %s is not supported" % loss,
                         "[loss_functions.py] Supported loss functions are:",
                         loss_dictionary.keys()
                         )
    
    function = loss_dictionary[loss]["function"]
    args = tuple([loss_hyperparams[arg] for arg in loss_dictionary[loss]["args"]])
    return function(args)
