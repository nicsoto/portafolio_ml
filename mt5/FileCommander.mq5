//+------------------------------------------------------------------+
//|                                              FileCommander.mq5   |
//|                        Lee comandos de archivo y ejecuta trades  |
//+------------------------------------------------------------------+
#property copyright "Trading Bot"
#property link      ""
#property version   "1.00"
#property strict

// Configuración
input string CommandFile = "python_commands.txt";
input string ResponseFile = "mt5_response.txt";
input bool EnableLogging = true;

//+------------------------------------------------------------------+
//| Expert initialization                                             |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("FileCommander iniciado");
   Print("Esperando comandos en: ", TerminalInfoString(TERMINAL_DATA_PATH), "\\MQL5\\Files\\", CommandFile);
   EventSetMillisecondTimer(500);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization                                           |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Print("FileCommander detenido");
}

//+------------------------------------------------------------------+
//| Timer - revisa archivo de comandos                                |
//+------------------------------------------------------------------+
void OnTimer()
{
   // Verificar si existe archivo de comandos
   if(!FileIsExist(CommandFile))
      return;
   
   // Leer comando
   int handle = FileOpen(CommandFile, FILE_READ|FILE_TXT|FILE_ANSI);
   if(handle == INVALID_HANDLE)
      return;
   
   string command = FileReadString(handle);
   FileClose(handle);
   
   // Borrar archivo para no repetir
   FileDelete(CommandFile);
   
   if(command == "")
      return;
   
   if(EnableLogging)
      Print("Comando recibido: ", command);
   
   // Procesar y responder
   string response = ProcessCommand(command);
   WriteResponse(response);
}

//+------------------------------------------------------------------+
//| Procesar comando                                                  |
//+------------------------------------------------------------------+
string ProcessCommand(string cmd)
{
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
      Print("Trade OK: ", sym, " ", EnumToString(type));
      return StringFormat("{\"status\":\"ok\",\"order_id\":%d,\"price\":%.5f}", 
                         result.order, result.price);
   }
   
   Print("Trade ERROR: ", GetLastError());
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
               return "{\"status\":\"ok\",\"message\":\"closed\"}";
         }
      }
   }
   return "{\"status\":\"error\",\"message\":\"no position\"}";
}

//+------------------------------------------------------------------+
//| Info de cuenta                                                    |
//+------------------------------------------------------------------+
string GetAccountInfo()
{
   return StringFormat(
      "{\"status\":\"ok\",\"balance\":%.2f,\"equity\":%.2f,\"margin\":%.2f}",
      AccountInfoDouble(ACCOUNT_BALANCE),
      AccountInfoDouble(ACCOUNT_EQUITY),
      AccountInfoDouble(ACCOUNT_MARGIN)
   );
}

//+------------------------------------------------------------------+
//| Posiciones                                                        |
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
         result += StringFormat(
            "{\"symbol\":\"%s\",\"volume\":%.2f,\"profit\":%.2f}",
            PositionGetString(POSITION_SYMBOL),
            PositionGetDouble(POSITION_VOLUME),
            PositionGetDouble(POSITION_PROFIT)
         );
      }
   }
   
   result += "]}";
   return result;
}

//+------------------------------------------------------------------+
//| Extraer valor JSON                                                |
//+------------------------------------------------------------------+
string GetJsonValue(string json, string key)
{
   string search = "\"" + key + "\":";
   int pos = StringFind(json, search);
   if(pos < 0) return "";
   
   int start = pos + StringLen(search);
   
   while(start < StringLen(json) && StringGetCharacter(json, start) == ' ')
      start++;
   
   if(StringGetCharacter(json, start) == '"')
   {
      start++;
      int end = StringFind(json, "\"", start);
      if(end < 0) return "";
      return StringSubstr(json, start, end - start);
   }
   
   int end = start;
   while(end < StringLen(json))
   {
      ushort c = StringGetCharacter(json, end);
      if(c == ',' || c == '}') break;
      end++;
   }
   
   return StringSubstr(json, start, end - start);
}

//+------------------------------------------------------------------+
//| Escribir respuesta                                                |
//+------------------------------------------------------------------+
void WriteResponse(string response)
{
   int handle = FileOpen(ResponseFile, FILE_WRITE|FILE_TXT|FILE_ANSI);
   if(handle != INVALID_HANDLE)
   {
      FileWriteString(handle, response);
      FileClose(handle);
      if(EnableLogging)
         Print("Respuesta: ", response);
   }
}
