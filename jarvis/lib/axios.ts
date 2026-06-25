import axios from "axios";

export const axios_targetr = axios.create({
  baseURL: process.env.URL_TARGETR,
  auth: {
    username: process.env.USERNAME_TARGETR!,
    password: process.env.PASSWORD_TARGETR!,
  },
});