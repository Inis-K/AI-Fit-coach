# AI Coach Mobilapp (React Native / Expo)

Detta är ett enkelt Expo-projekt som ansluter mot Flask-backendet för att demonstrera arbetsflödet i appen. Funktionen omfattar:

- Registrering / inloggning (demo utan tokenhantering)
- Uppsättning av tränings- och kostpreferenser
- Hämtning av träningspass och måltidsplaner baserat på mål och kosttyp
- Simulerad identifiering av träningsmaskiner genom etiketter
- Prenumerationsväxling och hämtning av dagens reklam

## Kom igång

1. Installera beroenden:

   ```bash
   npm install
   # eller
   yarn
   ```

2. Starta utvecklingsservern:

   ```bash
   npm run start
   ```

3. Kör appen på iOS- eller Android-enhet (Expo Go) och uppdatera `API_BASE` i `App.tsx` vid behov så att den pekar på backendens nätverksadress.

## Vidareutveckling

- Integrera riktig bildigenkänning (t.ex. TensorFlow Lite, CoreML eller moln-API) och skicka resultatet som `labels` till `/api/machines/identify`.
- Implementera riktig autentisering (token / sessioner).
- Bygg ut betalflöden via App Store / Google Play.
- Lägg till lokal datalagring för offline-läge och loggning av genomförda pass.
