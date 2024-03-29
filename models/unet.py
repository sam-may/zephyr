import tensorflow.keras as keras
from . import loss_functions

def std_conv(name, input_img, n_layers, n_filters, kernel_size, max_pool=2, 
             dropout=0.25, batch_norm=True, activation='elu', conv_dict={}):
    # Input
    conv = input_img
    # Convolution layers
    for i in range(n_layers):
        conv = keras.layers.Conv2D(
            n_filters, 
            kernel_size=kernel_size,
            activation=activation,
            kernel_initializer='lecun_uniform',
            padding='same',
            kernel_constraint=keras.constraints.max_norm(10),
            name='std_conv_%s_%d' % (name, i)
        )(conv)

        if dropout > 0:
            conv = keras.layers.Dropout(
                dropout, 
                name='std_conv_dropout_%s_%d' % (name, i)
            )(conv)

        if batch_norm:
            conv = keras.layers.BatchNormalization()(conv)
    # Store conv layer for lateral info transfer
    if conv_dict: 
        # Store the conv before applying max pooling, so it can be 
        # used later to help give higher resolution information in 
        # the up_convs
        conv_dict['std_conv_%s' % name] = conv
    # Max pooling layer (down-sampling)
    if max_pool >= 2:
        conv = keras.layers.MaxPooling2D(
            pool_size=(max_pool,max_pool), 
            name='std_conv_maxpool_%s' % name
        )(conv)
    
    return conv

def up_conv(name, input_img, n_layers, n_filters, kernel_size, aux_image=None, 
            dropout=0.25, batch_norm=False):

    conv = input_img

    for i in range(n_layers):
        conv = keras.layers.Conv2DTranspose(
            n_filters, 
            kernel_size,
            strides=2,
            padding='same',
            kernel_constraint=keras.constraints.max_norm(10),
            name='up_conv_%s_%d' % (name, i)
        )(conv)

        if dropout > 0:
            conv = keras.layers.Dropout(
                dropout, 
                name='up_conv_dropout_%s_%d' % (name, i)
            )(conv)

        if batch_norm:
            conv = keras.layers.BatchNormalization()(conv)

    if aux_image is not None:
        conv = keras.layers.Concatenate()([conv, aux_image])

    return conv
    
def unet2p5D(config, verbose=True):
    # Unpack config
    input_shape = config["input_shape"]
    n_filters = config["n_filters"]
    n_layers_conv = config["n_layers_conv"]
    n_layers_unet = config["n_layers_unet"]
    kernel_size = config["kernel_size"]
    dropout = config["dropout"]
    batch_norm = config["batch_norm"]
    learning_rate = config["learning_rate"]

    loss_hyperparams = { 
        "bce_alpha" : config["bce_alpha"],
        "dice_smooth" : config["dice_smooth"]
    }

    loss_function = getattr(loss_functions, config["loss_function"])

    # Set up input
    input_img = keras.layers.Input(shape=input_shape, name='input_img')
    conv = input_img
    conv_dict = {'input_img': conv}
    # Construct UNET
    for i in range(n_layers_unet):
        conv = std_conv(
            str(i), 
            conv, 
            n_layers_conv, 
            n_filters*(2**i), 
            kernel_size, 
            dropout=dropout, 
            conv_dict=conv_dict, 
            batch_norm=batch_norm
        )
    conv = std_conv(
        'bottom_conv', 
        conv, 
        n_layers_conv, 
        n_filters*(2**n_layers_unet), 
        kernel_size, 
        1, 
        dropout=dropout, 
        batch_norm=batch_norm
    )
    for i in range(n_layers_unet):
        conv = up_conv(
            str(i), 
            conv, 
            1, 
            n_filters, 
            kernel_size, 
            conv_dict['std_conv_%d' % (n_layers_unet - (i+1))], 
            dropout=dropout
        )
        conv = std_conv(
            'lateral_%s' % i, 
            conv, 
            n_layers_conv, 
            n_filters*(2**(n_layers_unet - (i+1))), 
            kernel_size, 
            1, 
            dropout=dropout, 
            batch_norm=batch_norm
        )
    # Output layer
    output = std_conv(
        'out', 
        conv, 
        1, 
        1, 
        kernel_size, 
        1, 
        dropout=0, 
        batch_norm=False, 
        activation='sigmoid'
    ) 
    # Put model together
    model = keras.models.Model(inputs=[input_img], outputs=[output])
    optimizer = keras.optimizers.Adam(lr=learning_rate)
    model.compile(
        optimizer=optimizer, 
        loss=loss_function(**loss_hyperparams),
        metrics=[
            'accuracy',
            loss_functions.dice_loss(**loss_hyperparams),
            loss_functions.weighted_crossentropy(**loss_hyperparams)
        ]
    )

    if verbose:
        print(model.summary())

    return model

