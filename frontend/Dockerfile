FROM node:24

COPY package.json .
RUN npm install
COPY . .

EXPOSE 5173
ENTRYPOINT ["npm", "run", "dev"]