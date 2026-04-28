FROM nginx:1.27-alpine

WORKDIR /usr/share/nginx/html

RUN rm -rf ./*

COPY index.html ./
COPY *.js ./
COPY *.css ./
COPY sample_vouchers ./sample_vouchers
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
