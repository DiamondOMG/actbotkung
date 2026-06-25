export const floatTo16BitPCM = (input: Float32Array): Int16Array => {
  const output = new Int16Array(input.length);
  for (let i = 0; i < input.length; i++) {
    output[i] = Math.max(-1, Math.min(1, input[i])) * 0x7fff;
  }
  return output;
};

export const base64ToFloat32 = (base64: string): Float32Array => {
  const binary = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
  const int16 = new Int16Array(binary.buffer);
  const float32 = new Float32Array(int16.length);
  for (let i = 0; i < int16.length; i++) {
    float32[i] = int16[i] / 32768;
  }
  return float32;
};

export const floatToBase64PCM = (float32: Float32Array): string => {
  const int16 = floatTo16BitPCM(float32);
  return btoa(String.fromCharCode(...new Uint8Array(int16.buffer)));
};
