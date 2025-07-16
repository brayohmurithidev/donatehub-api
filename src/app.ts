import express from 'express';
import {errorHandler} from "./middlewares/errorHandler";
import routesEntry from './routes/index';

const app = express();


app.use(express.json());

//ROUTES
app.use('/api/v1', routesEntry);

//GLOBAL ERROR HANDLER
app.use(errorHandler)

export default  app;