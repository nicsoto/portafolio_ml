//+------------------------------------------------------------------+
//|                                              SocketServer.mq5    |
//|                        Socket Server para recibir órdenes Python |
//|                           Escucha en puerto 5555 por defecto     |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.00"
#property strict

// Configuración
input int    ServerPort = 5555;       // Puerto del servidor
input int    MaxClients = 1;          // Máximo de clientes
input bool   EnableLogging = true;    // Habilitar logs

// Variables globales
int serverSocket = INVALID_HANDLE;
int clientSocket = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                     |
//+------------------------------------------------------------------+
int OnInit()
{
   // Crear socket del servidor
   serverSocket = SocketCreate();
   if(serverSocket == INVALID_HANDLE)
   {
      Print("Error creando socket: ", GetLastError());
      return(INIT_FAILED);
   }
   
   // Bind al puerto
   if(!SocketBind(serverSocket, "0.0.0.0", ServerPort))
   {
      Print("Error en bind puerto ", ServerPort, ": ", GetLastError());
      SocketClose(serverSocket);
      return(INIT_FAILED);
   }
   
   // Escuchar conexiones
   if(!SocketListen(serverSocket, MaxClients))
   {
      Print("Error en listen: ", GetLastError());
      SocketClose(serverSocket);
      return(INIT_FAILED);
   }
   
   Print("🚀 Socket Server iniciado en puerto ", ServerPort);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                   |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   if(clientSocket != INVALID_HANDLE)
      SocketClose(clientSocket);
   if(serverSocket != INVALID_HANDLE)
      SocketClose(serverSocket);
   Print("Socket Server cerrado");
}

//+------------------------------------------------------------------+
//| Expert tick function                                               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Intentar aceptar nueva conexión
   if(clientSocket == INVALID_HANDLE)
   {
      clientSocket = SocketAccept(serverSocket, 100);
      if(clientSocket != INVALID_HANDLE)
         Print("✅ Cliente conectado");
   }
   
   // Si hay cliente, leer comandos
   if(clientSocket != INVALID_HANDLE)
   {
      uchar buffer[];
      int bytesRead = SocketRead(clientSocket, buffer, 1024, 100);
      
      if(bytesRead > 0)
      {
         string command = CharArrayToString(buffer, 0, bytesRead);
         if(EnableLogging)
            Print("📨 Recibido: ", command);
         
         string response = ProcessCommand(command);
         SendResponse(response);
      }
      else if(bytesRead == 0)
      {
         // Cliente desconectado
         SocketClose(clientSocket);
         clientSocket = INVALID_HANDLE;
         Print("Cliente desconectado");
      }
   }
}

//+------------------------------------------------------------------+
//| Procesar comando JSON                                             |
//+------------------------------------------------------------------+
string ProcessCommand(string jsonCommand)
{
   // Parsear JSON simple: {"action": "buy/sell/close", "symbol": "EURUSD", "volume": 0.1}
   
   string action = ExtractJsonValue(jsonCommand, "action");
   string symbol = ExtractJsonValue(jsonCommand, "symbol");
   double volume = StringToDouble(ExtractJsonValue(jsonCommand, "volume"));
   
   if(action == "")
      return "{\"status\": \"error\", \"message\": \"No action specified\"}";
   
   // Ejecutar acción
   if(action == "buy")
      return ExecuteBuy(symbol, volume);
   else if(action == "sell")
      return ExecuteSell(symbol, volume);
   else if(action == "close")
      return ClosePosition(symbol);
   else if(action == "account")
      return GetAccountInfo();
   else if(action == "positions")
      return GetPositions();
   else if(action == "ping")
      return "{\"status\": \"ok\", \"message\": \"pong\"}";
   
   return "{\"status\": \"error\", \"message\": \"Unknown action\"}";
}

//+------------------------------------------------------------------+
//| Ejecutar compra                                                   |
//+------------------------------------------------------------------+
string ExecuteBuy(string symbol, double volume)
{
   if(symbol == "") symbol = Symbol();
   if(volume <= 0) volume = 0.01;
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = volume;
   request.type = ORDER_TYPE_BUY;
   request.price = SymbolInfoDouble(symbol, SYMBOL_ASK);
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "Python Bot";
   
   if(OrderSend(request, result))
   {
      Print("✅ BUY ejecutado: ", symbol, " Vol: ", volume);
      return StringFormat("{\"status\": \"ok\", \"order_id\": %d, \"price\": %.5f}", 
                         result.order, result.price);
   }
   else
   {
      Print("❌ Error BUY: ", GetLastError());
      return StringFormat("{\"status\": \"error\", \"code\": %d}", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Ejecutar venta                                                    |
//+------------------------------------------------------------------+
string ExecuteSell(string symbol, double volume)
{
   if(symbol == "") symbol = Symbol();
   if(volume <= 0) volume = 0.01;
   
   MqlTradeRequest request = {};
   MqlTradeResult result = {};
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = symbol;
   request.volume = volume;
   request.type = ORDER_TYPE_SELL;
   request.price = SymbolInfoDouble(symbol, SYMBOL_BID);
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "Python Bot";
   
   if(OrderSend(request, result))
   {
      Print("✅ SELL ejecutado: ", symbol, " Vol: ", volume);
      return StringFormat("{\"status\": \"ok\", \"order_id\": %d, \"price\": %.5f}", 
                         result.order, result.price);
   }
   else
   {
      Print("❌ Error SELL: ", GetLastError());
      return StringFormat("{\"status\": \"error\", \"code\": %d}", GetLastError());
   }
}

//+------------------------------------------------------------------+
//| Cerrar posición                                                   |
//+------------------------------------------------------------------+
string ClosePosition(string symbol)
{
   if(symbol == "") symbol = Symbol();
   
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(PositionGetString(POSITION_SYMBOL) == symbol)
         {
            MqlTradeRequest request = {};
            MqlTradeResult result = {};
            
            request.action = TRADE_ACTION_DEAL;
            request.symbol = symbol;
            request.volume = PositionGetDouble(POSITION_VOLUME);
            request.position = PositionGetTicket(i);
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
               request.type = ORDER_TYPE_SELL;
               request.price = SymbolInfoDouble(symbol, SYMBOL_BID);
            }
            else
            {
               request.type = ORDER_TYPE_BUY;
               request.price = SymbolInfoDouble(symbol, SYMBOL_ASK);
            }
            
            request.deviation = 10;
            
            if(OrderSend(request, result))
            {
               Print("✅ Posición cerrada: ", symbol);
               return "{\"status\": \"ok\", \"message\": \"Position closed\"}";
            }
         }
      }
   }
   
   return "{\"status\": \"error\", \"message\": \"No position found\"}";
}

//+------------------------------------------------------------------+
//| Obtener info de cuenta                                            |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat(
      "{\"status\": \"ok\", \"balance\": %.2f, \"equity\": %.2f, \"margin\": %.2f, \"free_margin\": %.2f}",
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE)
   );
}

//+------------------------------------------------------------------+
//| Obtener posiciones abiertas                                       |
//+------------------------------------------------------------------+
string GetPositions()
{
   string result = "{\"status\": \"ok\", \"positions\": [";
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      if(PositionSelectByTicket(PositionGetTicket(i)))
      {
         if(i > 0) result += ",";
         result += StringFormat(
            "{\"symbol\": \"%s\", \"volume\": %.2f, \"profit\": %.2f, \"type\": \"%s\"}",
            PositionGetString(POSITION_SYMBOL),
            PositionGetDouble(POSITION_VOLUME),
            PositionGetDouble(POSITION_PROFIT),
            PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell"
         );
      }
   }
   
   result += "]}";
   return result;
}

//+------------------------------------------------------------------+
//| Extraer valor de JSON simple                                      |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
   string searchKey = "\"" + key + "\"";
   int keyPos = StringFind(json, searchKey);
   if(keyPos < 0) return "";
   
   int colonPos = StringFind(json, ":", keyPos);
   if(colonPos < 0) return "";
   
   int startPos = colonPos + 1;
   
   // Saltar espacios
   while(StringGetCharacter(json, startPos) == ' ')
      startPos++;
   
   // Si es string (empieza con ")
   if(StringGetCharacter(json, startPos) == '"')
   {
      startPos++;
      int endPos = StringFind(json, "\"", startPos);
      if(endPos < 0) return "";
      return StringSubstr(json, startPos, endPos - startPos);
   }
   
   // Si es número
   int endPos = startPos;
   while(endPos < StringLen(json))
   {
      int c = StringGetCharacter(json, endPos);
      if(c == ',' || c == '}' || c == ' ')
         break;
      endPos++;
   }
   
   return StringSubstr(json, startPos, endPos - startPos);
}

//+------------------------------------------------------------------+
//| Enviar respuesta al cliente                                       |
//+------------------------------------------------------------------+
void SendResponse(string response)
{
   if(clientSocket == INVALID_HANDLE) return;
   
   uchar buffer[];
   StringToCharArray(response, buffer);
   SocketSend(clientSocket, buffer, ArraySize(buffer) - 1);  // -1 para quitar null terminator
   
   if(EnableLogging)
      Print("📤 Enviado: ", response);
}
