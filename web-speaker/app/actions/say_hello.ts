'use server';

export async function say_hello() {
  console.log('สวัสดีชาวโลก');
  return { message: 'Greeting sent from server' };
}
