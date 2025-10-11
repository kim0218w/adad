###########################
# 학습 효과 분석
###########################
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras import layers
from tensorflow.keras.layers import Input, Dense, Conv2D, MaxPooling2D, UpSampling2D
from tensorflow.keras.datasets import mnist
from tensorflow.keras.callbacks import Callback, EarlyStopping

#########################################################
# Convolutional layer based AE with MNIST, Models/Class
######################################################

def Conv2D(filters, kernel_size, padding='same', activation='relu'):
    return tf.keras.layers.Conv2D(filters, kernel_size, padding=padding, activation=activation)


class AE(tf.keras.Model):
    def __init__(self, org_shape=(1, 28, 28)):
        # Input
        original = tf.keras.layers.Input(shape=org_shape)

        # encoding-1
        x = Conv2D(32, (3, 3))(original)
        x = Conv2D(32, (3, 3))(x)
        x = tf.keras.layers.MaxPooling2D((2, 2), padding='same')(x)

        # encoding-2
        x = Conv2D(64, (3, 3))(x)
        x = Conv2D(64, (3, 3))(x)
        x = tf.keras.layers.MaxPooling2D((2, 2), padding='same')(x)

        # encoding-3
        z = Conv2D(128, (3, 3))(x)

        # decoding-1
        y = Conv2D(64, (3, 3))(z)
        y = tf.keras.layers.UpSampling2D((2, 2))(y)
        y = Conv2D(64, (3, 3))(y)

        # decoding-2
        y = Conv2D(32, (3, 3))(y)
        y = tf.keras.layers.UpSampling2D((2, 2))(y)
        y = Conv2D(32, (3, 3))(y)

        # decoding-3
        y = Conv2D(16, (3, 3))(y)

        # decoding & Output
        decoded = Conv2D(1, (3, 3), activation='sigmoid')(y)

        super().__init__(original, decoded)
        self.compile(optimizer='adadelta', loss='binary_crossentropy', metrics=['accuracy'])

###########################
# 데이타 불러오기
###########################
class DATA:
    def __init__(self, noise_factor=0.2):
        (x_train, _), (x_test, _) = mnist.load_data()

        x_train = tf.convert_to_tensor(x_train, dtype=tf.float32) / 255.0
        x_test = tf.convert_to_tensor(x_test, dtype=tf.float32) / 255.0

        if tf.keras.backend.image_data_format() == "channels_first":
            x_train = tf.reshape(x_train, (tf.shape(x_train)[0], 1, 28, 28))
            x_test = tf.reshape(x_test, (tf.shape(x_test)[0], 1, 28, 28))
        else:
            x_train = tf.reshape(x_train, (tf.shape(x_train)[0], 28, 28, 1))
            x_test = tf.reshape(x_test, (tf.shape(x_test)[0], 28, 28, 1))

        noise_train = noise_factor * tf.random.normal(tf.shape(x_train), dtype=tf.float32)
        noise_test = noise_factor * tf.random.normal(tf.shape(x_test), dtype=tf.float32)

        x_train_noisy = tf.clip_by_value(x_train + noise_train, 0.0, 1.0)
        x_test_noisy = tf.clip_by_value(x_test + noise_test, 0.0, 1.0)

        self.x_train = x_train
        self.x_test = x_test
        self.x_train_noisy = x_train_noisy
        self.x_test_noisy = x_test_noisy
        self.input_shape = x_train.shape[1:]


def show_ae(autoencoder, data, sample_count=10):
    x_test_clean = data.x_test
    x_test_noisy = data.x_test_noisy
    decoded_imgs = autoencoder.predict(x_test_noisy)

    if tf.keras.backend.image_data_format() == 'channels_first':
        N, n_ch, n_i, n_j = x_test_clean.shape
        x_test_clean = tf.reshape(x_test_clean, (N, n_i, n_j))
        x_test_noisy = tf.reshape(x_test_noisy, (N, n_i, n_j))
        decoded_imgs = decoded_imgs.reshape(decoded_imgs.shape[0], n_i, n_j)
    else:
        N, n_i, n_j, n_ch = x_test_clean.shape
        x_test_clean = tf.reshape(x_test_clean, (N, n_i, n_j))
        x_test_noisy = tf.reshape(x_test_noisy, (N, n_i, n_j))
        decoded_imgs = decoded_imgs.reshape(decoded_imgs.shape[0], n_i, n_j)

    x_clean_np = x_test_clean.numpy()
    x_noisy_np = x_test_noisy.numpy()

    plt.figure(figsize=(16, 5))
    for i in range(sample_count):
        ax = plt.subplot(3, sample_count, i + 1)
        plt.imshow(x_clean_np[i], cmap='gray')
        ax.set_title("Clean")
        ax.axis("off")

        ax = plt.subplot(3, sample_count, i + 1 + sample_count)
        plt.imshow(x_noisy_np[i], cmap='gray')
        ax.set_title("Noisy")
        ax.axis("off")

        ax = plt.subplot(3, sample_count, i + 1 + 2 * sample_count)
        plt.imshow(decoded_imgs[i], cmap='gray')
        ax.set_title("Denoised")
        ax.axis("off")

    plt.tight_layout()
    plt.show()
    

###########################
# 학습 및 확인
###########################
def main(epochs=20, batch_size=128):
    data = DATA()
    autoencoder = AE(data.input_shape)

    history = autoencoder.fit(
        data.x_train_noisy,
        data.x_train,
        epochs=epochs,
        batch_size=batch_size,
        shuffle=True,
        validation_data=(data.x_test_noisy, data.x_test)
    )

    try:
        tf.keras.utils.plot_model(autoencoder, to_file='model.png', show_shapes=True)
        plt.show()
    except (ImportError, AttributeError, OSError) as err:
        print("모델 구조 시각화를 건너뜁니다. pydot과 graphviz를 설치하면 표시됩니다.")
        print(err)

    show_ae(autoencoder, data)
    plt.show()


if __name__ == '__main__':
    main()
