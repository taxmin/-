import onnxruntime

class PredictBase(object):
    def __init__(self):
        pass

    def get_onnx_session(self, model_dir, use_gpu):
        self.available_providers = onnxruntime.get_available_providers()
        # # 使用gpu
        # if use_gpu:
        #     providers =[('CUDAExecutionProvider',{"cudnn_conv_algo_search": "DEFAULT"}),'CPUExecutionProvider']
        # else:
        #     providers =['CPUExecutionProvider']
        if use_gpu:
            # 优先尝试DML（DirectML），然后CUDA，最后CPU
            preferred_providers = []

            if 'DmlExecutionProvider' in self.available_providers:
                preferred_providers.append('DmlExecutionProvider')
            elif 'CUDAExecutionProvider' in self.available_providers:
                preferred_providers.append('CUDAExecutionProvider')
            elif 'CPUExecutionProvider' in self.available_providers:
                preferred_providers.append('CPUExecutionProvider')

            # 确保有CPU回退
            # preferred_providers.append('CPUExecutionProvider')
            providers = preferred_providers
        else:
            providers = ['CPUExecutionProvider']
        print(providers)
        onnx_session = onnxruntime.InferenceSession(model_dir, None,providers=providers)

        # print("providers:", onnxruntime.get_device())
        return onnx_session


    def get_output_name(self, onnx_session):
        """
        output_name = onnx_session.get_outputs()[0].name
        :param onnx_session:
        :return:
        """
        output_name = []
        for node in onnx_session.get_outputs():
            output_name.append(node.name)
        return output_name

    def get_input_name(self, onnx_session):
        """
        input_name = onnx_session.get_inputs()[0].name
        :param onnx_session:
        :return:
        """
        input_name = []
        for node in onnx_session.get_inputs():
            input_name.append(node.name)
        return input_name

    def get_input_feed(self, input_name, image_numpy):
        """
        input_feed={self.input_name: image_numpy}
        :param input_name:
        :param image_numpy:
        :return:
        """
        input_feed = {}
        for name in input_name:
            input_feed[name] = image_numpy
        return input_feed
