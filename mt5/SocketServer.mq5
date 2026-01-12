//+------------------------------------------------------------------+
//|                                              SocketServer.mq5    |
//|                        Socket Server para recibir órdenes Python |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.00"
#property strict

// Configuración
input int ServerPort = 5555;
input bool EnableLogging = true;

// Variables globales
int serverSocket = -1;
int clientSocket = -1;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   // Crear socket
   serverSocket = SocketCreate();
   if(serverSocket < 0)
   {
      Print("Error creando socket: ", GetLastError());
      return INIT_FAILED;
   }
   
   // Bind al puerto
   if(!SocketBind(serverSocket, "127.0.0.1", ServerPort))
   {
      Print("Error en bind: ", GetLastError());
      SocketClose(serverSocket);
      return INIT_FAILED;
   }
   
   // Escuchar
   if(!SocketListen(serverSocket, 1))
   {
      Print("Error en listen: ", GetLastError());
      SocketClose(serverSocket);
      return INIT_FAILED;
   }
   
   Print("Socket Server iniciado en puerto ", ServerPort);
   EventSetMillisecondTimer(100);
   
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   if(clientSocket >= 0) SocketClose(clientSocket);
   if(serverSocket >= 0) SocketClose(serverSocket);
   Print("Socket Server cerrado");
}

//+------------------------------------------------------------------+
//| Timer function                                                    |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Aceptar nueva conexión
   if(clientSocket < 0)
   {
      clientSocket = SocketAccept(serverSocket, 100);
      if(clientSocket >= 0)
         Print("Cliente conectado");
   }
   
   // Leer datos del cliente
   if(clientSocket >= 0)
   {
      uchar buffer[];
      int len = SocketRead(clientSocket, buffer, 1024, 100);
      
      if(len > 0)
      {
         string command = CharArrayToString(buffer, 0, len);
         if(EnableLogging) Print("Recibido: ", command);
         
         string response = ProcessCommand(command);
         SendResponse(response);
      }
      else if(len == 0)
      {
         // Cliente desconectado
         SocketClose(clientSocket);
         clientSocket = -1;
         Print("Cliente desconectado");
      }
   }
}

//+------------------------------------------------------------------+
//| Procesar comando                                                  |
//+------------------------------------------------------------------+
string ProcessCommand(string cmd)
{
   // Extraer valores del JSON simple
   string action = GetJsonValue(cmd, "action");
   string symbol = GetJsonValue(cmd, "symbol");
   double volume = StringToDouble(GetJsonValue(cmd, "volume"));
   
   if(symbol == "") symbol = Symbol();
   if(volume <= 0) volume = 0.01;
   
   if(action == "ping")
      return "{\"status\":\"ok\",\"message\":\"pong\"}";
   
   if(action == "account")
      return GetAccountInfo();
   
   if(action == "positions")
      return GetPositions();
   
   if(action == "buy")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_BUY);
   
   if(action == "sell")
      return ExecuteTrade(symbol, volume, ORDER_TYPE_SELL);
   
   if(action == "close")
      return ClosePos(symbol);
   
   return "{\"status\":\"error\",\"message\":\"Unknown action\"}";
}

//+------------------------------------------------------------------+
//| Ejecutar trade                                                    |
//+------------------------------------------------------------------+
string ExecuteTrade(string sym, double vol, ENUM_ORDER_TYPE type)
{
   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);
   
   request.action = TRADE_ACTION_DEAL;
   request.symbol = sym;
   request.volume = vol;
   request.type = type;
   request.deviation = 10;
   request.magic = 123456;
   request.comment = "PythonBot";
   
   if(type == ORDER_TYPE_BUY)
      request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
   else
      request.price = SymbolInfoDouble(sym, SYMBOL_BID);
   
   if(OrderSend(request, result))
   {
      Print("Trade ejecutado: ", sym, " ", EnumToString(type));
      return StringFormat("{\"status\":\"ok\",\"order_id\":%d,\"price\":%.5f}", 
                         result.order, result.price);
   }
   
   Print("Error trade: ", GetLastError());
   return StringFormat("{\"status\":\"error\",\"code\":%d}", GetLastError());
}

//+------------------------------------------------------------------+
//| Cerrar posición                                                   |
//+------------------------------------------------------------------+
string ClosePos(string sym)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(PositionGetString(POSITION_SYMBOL) == sym)
         {
            MqlTradeRequest request;
            MqlTradeResult result;
            ZeroMemory(request);
            ZeroMemory(result);
            
            request.action = TRADE_ACTION_DEAL;
            request.symbol = sym;
            request.volume = PositionGetDouble(POSITION_VOLUME);
            request.position = ticket;
            request.deviation = 10;
            
            if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY)
            {
               request.type = ORDER_TYPE_SELL;
               request.price = SymbolInfoDouble(sym, SYMBOL_BID);
            }
            else
            {
               request.type = ORDER_TYPE_BUY;
               request.price = SymbolInfoDouble(sym, SYMBOL_ASK);
            }
            
            if(OrderSend(request, result))
               return "{\"status\":\"ok\",\"message\":\"Position closed\"}";
         }
      }
   }
   return "{\"status\":\"error\",\"message\":\"No position found\"}";
}

//+------------------------------------------------------------------+
//| Info de cuenta                                                    |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat(
      "{\"status\":\"ok\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f,\"free_margin\":%.2f}",
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN),
      AccountInfoDouble(ACCOUNT_MARGIN_FREE)
   );
}

//+------------------------------------------------------------------+
//| Posiciones abiertas                                               |
//+------------------------------------------------------------------+
string GetPositions()
{
   string result = "{\"status\":\"ok\",\"positions\":[";
   
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionSelectByTicket(ticket))
      {
         if(i > 0) result += ",";
         string posType = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "buy" : "sell";
         result += StringFormat(
            "{\"symbol\":\"%s\",\"volume\":%.2f,\"profit\":%.2f,\"type\":\"%s\"}",
            PositionGetString(POSITION_SYMBOL),
            PositionGetDouble(POSITION_VOLUME),
            PositionGetDouble(POSITION_PROFIT),
            posType
         );
      }
   }
   
   result += "]}";
   return result;
}

//+------------------------------------------------------------------+
//| Extraer valor de JSON                                             |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
   string search = "\"" + key + "\"";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   
   int colonPos = StringFind(json, ":", pos);
   if(colonPos < 0) return "";
   
   int start = colonPos + 1;
   
   // Saltar espacios
   while(start < StringLen(json) && StringGetCharacter(json, start) == ' ')
      start++;
   
   // Si es string
   if(StringGetCharacter(json, start) == '"')
   {
      start++;
      int end = StringFind(json, "\"", start);
      if(end < 0) return "";
      return StringSubstr(json, start, end - start);
   }
   
   // Si es número
   int end = start;
   while(end < StringLen(json))
   {
      ushort c = StringGetCharacter(json, end);
      if(c == ',' || c == '}' || c == ' ') break;
      end++;
   }
   
   return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
//| Enviar respuesta                                                  |
//+------------------------------------------------------------------+
void SendResponse(string response)
{
   if(clientSocket < 0) return;
   
   uchar buffer[];
   int len = StringToCharArray(response, buffer) - 1;
   if(len > 0)
      SocketSend(clientSocket, buffer, len);
   
   if(EnableLogging) Print("Enviado: ", response);
}
