import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { StatusBar } from 'expo-status-bar';

const API_BASE = 'http://localhost:5000/api';

type WorkoutBlock = {
  title: string;
  description: string;
  duration_minutes: number;
  equipment: string;
  primary_muscles: string[];
  instructions: string[];
};

type Meal = {
  title: string;
  calories: number;
  protein: number;
  carbs: number;
  fats: number;
  instructions: string;
  diet_type: string;
};

type MachineGuide = {
  machine_name: string;
  primary_muscles: string[];
  cues: string[];
  instructions: string[];
  label: string;
};

type SubscriptionResponse = {
  tier: string;
  renewal_date: string | null;
};

const goals = [
  { label: 'Gå ner i vikt', value: 'lose_weight' },
  { label: 'Komma i form', value: 'get_fit' },
  { label: 'Bygga styrka', value: 'build_strength' },
];

const levels = [
  { label: 'Nybörjare', value: 'beginner' },
  { label: 'Medel', value: 'intermediate' },
];

const diets = [
  { label: 'Standard', value: 'standard' },
  { label: 'Vegetarisk', value: 'vegetarian' },
  { label: 'Högprotein', value: 'high_protein' },
];

const machineHints = [
  { label: 'Benpress', value: 'leg press' },
  { label: 'Latsdrag', value: 'lat pulldown' },
  { label: 'Roddmaskin', value: 'rowing machine' },
];

const fetchJson = async <T,>(url: string, options?: RequestInit) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Okänt fel' }));
    throw new Error(error.error || error.message || 'Okänt fel');
  }

  return (await response.json()) as T;
};

export default function App() {
  const [userId, setUserId] = useState<number | null>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('register');
  const [email, setEmail] = useState('demo@coach.se');
  const [password, setPassword] = useState('demo1234');
  const [name, setName] = useState('Demo Coach');

  const [selectedGoal, setSelectedGoal] = useState('lose_weight');
  const [selectedLevel, setSelectedLevel] = useState('beginner');
  const [selectedDiet, setSelectedDiet] = useState('standard');
  const [allergies, setAllergies] = useState('');

  const [workouts, setWorkouts] = useState<Record<string, WorkoutBlock[]>>({});
  const [meals, setMeals] = useState<Record<string, Meal[]>>({});
  const [totalCalories, setTotalCalories] = useState<number | null>(null);
  const [machineGuide, setMachineGuide] = useState<MachineGuide | null>(null);
  const [machineHint, setMachineHint] = useState(machineHints[0].value);
  const [advert, setAdvert] = useState<any | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionResponse | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canUseContent = useMemo(() => userId !== null, [userId]);

  const handleAuth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      if (authMode === 'register') {
        const data = await fetchJson<{ user_id: number }>(`${API_BASE}/users`, {
          method: 'POST',
          body: JSON.stringify({ email, password, name }),
        });
        setUserId(data.user_id);
        await fetchJson(`${API_BASE}/preferences`, {
          method: 'POST',
          body: JSON.stringify({
            user_id: data.user_id,
            primary_goal: selectedGoal,
            experience_level: selectedLevel,
            dietary_preference: selectedDiet,
            allergies: allergies
              .split(',')
              .map((item) => item.trim())
              .filter(Boolean),
          }),
        });
        await fetchSubscription(data.user_id);
      } else {
        const data = await fetchJson<{ user_id: number }>(`${API_BASE}/login`, {
          method: 'POST',
          body: JSON.stringify({ email, password }),
        });
        setUserId(data.user_id);
        await fetchSubscription(data.user_id);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [authMode, email, password, name, selectedGoal, selectedLevel, selectedDiet, allergies]);

  const fetchWorkouts = useCallback(async () => {
    if (!userId) {
      setError('Logga in först.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await fetchJson<{ plan: Record<string, WorkoutBlock[]> }>(
        `${API_BASE}/plan/workouts?user_id=${userId}&goal=${selectedGoal}&level=${selectedLevel}`,
      );
      setWorkouts(data.plan);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId, selectedGoal, selectedLevel]);

  const fetchMeals = useCallback(async () => {
    if (!userId) {
      setError('Logga in först.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await fetchJson<{
        plan: Record<string, Meal[]>;
        total_daily_calories: number;
      }>(`${API_BASE}/plan/meals?user_id=${userId}&goal=${selectedGoal}&diet_type=${selectedDiet}`);
      setMeals(data.plan);
      setTotalCalories(data.total_daily_calories);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId, selectedGoal, selectedDiet]);

  const identifyMachine = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchJson<MachineGuide>(`${API_BASE}/machines/identify`, {
        method: 'POST',
        body: JSON.stringify({ labels: [machineHint] }),
      });
      setMachineGuide(data);
    } catch (err: any) {
      setMachineGuide(null);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [machineHint]);

  const fetchAd = useCallback(async () => {
    if (!userId) {
      setError('Logga in först.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await fetchJson<{ ad?: any; message?: string }>(`${API_BASE}/ads/daily`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      });
      setAdvert(data.ad || null);
      if (data.message) {
        setError(data.message);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const fetchSubscription = useCallback(
    async (targetUserId?: number) => {
      const id = targetUserId ?? userId;
      if (!id) return;
      try {
        const data = await fetchJson<SubscriptionResponse>(`${API_BASE}/subscription/${id}`);
        setSubscription(data);
      } catch (err: any) {
        setSubscription(null);
        setError(err.message);
      }
    },
    [userId],
  );

  const toggleSubscription = useCallback(async () => {
    if (!userId) return;
    try {
      setLoading(true);
      setError(null);
      const nextTier = subscription?.tier === 'premium' ? 'ad-supported' : 'premium';
      await fetchJson(`${API_BASE}/subscription`, {
        method: 'POST',
        body: JSON.stringify({ user_id: userId, tier: nextTier }),
      });
      await fetchSubscription();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [userId, subscription, fetchSubscription]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.heading}>AI Coach</Text>
        <Text style={styles.subheading}>Personlig tränings- och kostplan</Text>

        <View style={styles.card}>
          <View style={styles.switchRow}>
            <TouchableOpacity
              style={[styles.switchButton, authMode === 'register' && styles.switchButtonActive]}
              onPress={() => setAuthMode('register')}
            >
              <Text style={styles.switchText}>Registrera</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.switchButton, authMode === 'login' && styles.switchButtonActive]}
              onPress={() => setAuthMode('login')}
            >
              <Text style={styles.switchText}>Logga in</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            autoCapitalize="none"
            keyboardType="email-address"
            placeholder="E-post"
            value={email}
            onChangeText={setEmail}
            style={styles.input}
          />
          <TextInput
            secureTextEntry
            placeholder="Lösenord"
            value={password}
            onChangeText={setPassword}
            style={styles.input}
          />
          {authMode === 'register' && (
            <TextInput placeholder="Namn" value={name} onChangeText={setName} style={styles.input} />
          )}
          <TouchableOpacity style={styles.primaryButton} onPress={handleAuth}>
            <Text style={styles.primaryButtonText}>
              {authMode === 'register' ? 'Skapa konto' : 'Logga in'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Preferenser</Text>
          <Text style={styles.helperText}>Används för att skapa planerna.</Text>

          <Picker selectedValue={selectedGoal} onValueChange={setSelectedGoal}>
            {goals.map((goal) => (
              <Picker.Item key={goal.value} label={goal.label} value={goal.value} />
            ))}
          </Picker>
          <Picker selectedValue={selectedLevel} onValueChange={setSelectedLevel}>
            {levels.map((level) => (
              <Picker.Item key={level.value} label={level.label} value={level.value} />
            ))}
          </Picker>
          <Picker selectedValue={selectedDiet} onValueChange={setSelectedDiet}>
            {diets.map((diet) => (
              <Picker.Item key={diet.value} label={diet.label} value={diet.value} />
            ))}
          </Picker>
          <TextInput
            placeholder="Allergier (kommaseparerat)"
            value={allergies}
            onChangeText={setAllergies}
            style={styles.input}
          />
        </View>

        {canUseContent && (
          <>
            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Träningsplan</Text>
              <TouchableOpacity style={styles.secondaryButton} onPress={fetchWorkouts}>
                <Text style={styles.secondaryButtonText}>Generera pass</Text>
              </TouchableOpacity>
              {Object.entries(workouts).map(([day, blocks]) => (
                <View key={day} style={styles.block}>
                  <Text style={styles.blockTitle}>{day.toUpperCase()}</Text>
                  {blocks.map((block, index) => (
                    <View key={`${day}-${index}`} style={styles.blockBody}>
                      <Text style={styles.blockHeading}>{block.title}</Text>
                      <Text style={styles.blockText}>{block.description}</Text>
                      <Text style={styles.blockMeta}>Tid: {block.duration_minutes} min</Text>
                      <Text style={styles.blockMeta}>Utrustning: {block.equipment}</Text>
                      <Text style={styles.blockMeta}>Muskler: {block.primary_muscles.join(', ')}</Text>
                      {block.instructions.map((step, stepIndex) => (
                        <Text key={stepIndex} style={styles.blockStep}>
                          • {step}
                        </Text>
                      ))}
                    </View>
                  ))}
                </View>
              ))}
            </View>

            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Måltidsplan</Text>
              <TouchableOpacity style={styles.secondaryButton} onPress={fetchMeals}>
                <Text style={styles.secondaryButtonText}>Hämta måltider</Text>
              </TouchableOpacity>
              {totalCalories !== null && (
                <Text style={styles.helperText}>Totalt: {totalCalories} kcal/dag</Text>
              )}
              {Object.entries(meals).map(([type, items]) => (
                <View key={type} style={styles.block}>
                  <Text style={styles.blockTitle}>{type.toUpperCase()}</Text>
                  {items.map((meal, index) => (
                    <View key={`${type}-${index}`} style={styles.blockBody}>
                      <Text style={styles.blockHeading}>{meal.title}</Text>
                      <Text style={styles.blockMeta}>Kalorier: {meal.calories}</Text>
                      <Text style={styles.blockMeta}>Protein: {meal.protein} g</Text>
                      <Text style={styles.blockMeta}>Kolhydrater: {meal.carbs} g</Text>
                      <Text style={styles.blockMeta}>Fett: {meal.fats} g</Text>
                      <Text style={styles.blockText}>{meal.instructions}</Text>
                    </View>
                  ))}
                </View>
              ))}
            </View>

            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Maskinidentifiering</Text>
              <Text style={styles.helperText}>
                I en riktig app skickar du etiketter från bildigenkänning hit.
              </Text>
              <Picker selectedValue={machineHint} onValueChange={setMachineHint}>
                {machineHints.map((hint) => (
                  <Picker.Item key={hint.value} label={hint.label} value={hint.value} />
                ))}
              </Picker>
              <TouchableOpacity style={styles.secondaryButton} onPress={identifyMachine}>
                <Text style={styles.secondaryButtonText}>Identifiera</Text>
              </TouchableOpacity>
              {machineGuide && (
                <View style={styles.block}>
                  <Text style={styles.blockTitle}>{machineGuide.machine_name}</Text>
                  <Text style={styles.blockMeta}>
                    Muskler: {machineGuide.primary_muscles.join(', ')}
                  </Text>
                  {machineGuide.instructions.map((step, index) => (
                    <Text key={index} style={styles.blockStep}>
                      • {step}
                    </Text>
                  ))}
                  <Text style={styles.helperText}>Tekniktips:</Text>
                  {machineGuide.cues.map((cue, index) => (
                    <Text key={index} style={styles.blockText}>
                      - {cue}
                    </Text>
                  ))}
                </View>
              )}
            </View>

            <View style={styles.card}>
              <Text style={styles.sectionTitle}>Prenumeration & annonser</Text>
              <Text style={styles.helperText}>
                Premium tar bort annonser och planerar om fakturering varje 30:e dag.
              </Text>
              <TouchableOpacity style={styles.secondaryButton} onPress={toggleSubscription}>
                <Text style={styles.secondaryButtonText}>
                  {subscription?.tier === 'premium' ? 'Nedgradera till reklam' : 'Uppgradera till premium'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.secondaryButton} onPress={fetchAd}>
                <Text style={styles.secondaryButtonText}>Hämta dagens reklam</Text>
              </TouchableOpacity>
              {subscription && (
                <Text style={styles.helperText}>
                  Aktuell nivå: {subscription.tier}{' '}
                  {subscription.renewal_date ? `(förnyas ${subscription.renewal_date})` : ''}
                </Text>
              )}
              {advert && (
                <View style={styles.block}>
                  <Text style={styles.blockTitle}>{advert.title}</Text>
                  <Text style={styles.blockText}>{advert.body}</Text>
                  <Text style={styles.helperText}>CTA: {advert.cta_label}</Text>
                </View>
              )}
            </View>
          </>
        )}

        {error && <Text style={styles.errorText}>{error}</Text>}
        {loading && <ActivityIndicator size="large" color="#1f78ff" />}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f4f6fb',
  },
  content: {
    padding: 16,
    paddingBottom: 32,
    gap: 16,
  },
  heading: {
    fontSize: 32,
    fontWeight: '700',
    textAlign: 'center',
    marginTop: 16,
    color: '#0d1b2a',
  },
  subheading: {
    fontSize: 16,
    textAlign: 'center',
    color: '#415a77',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
    gap: 12,
  },
  switchRow: {
    flexDirection: 'row',
    backgroundColor: '#eef2fb',
    borderRadius: 8,
    overflow: 'hidden',
  },
  switchButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
  },
  switchButtonActive: {
    backgroundColor: '#1f78ff',
  },
  switchText: {
    color: '#0d1b2a',
    fontWeight: '600',
  },
  input: {
    borderColor: '#d6d9e0',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
  },
  primaryButton: {
    backgroundColor: '#1f78ff',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#fff',
    fontWeight: '700',
    fontSize: 16,
  },
  secondaryButton: {
    backgroundColor: '#eef2fb',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#1f78ff',
    fontWeight: '600',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0d1b2a',
  },
  helperText: {
    color: '#5c677d',
    fontSize: 14,
  },
  block: {
    borderTopColor: '#d6d9e0',
    borderTopWidth: 1,
    paddingTop: 12,
    gap: 8,
  },
  blockBody: {
    backgroundColor: '#f8f9ff',
    borderRadius: 10,
    padding: 12,
    gap: 4,
  },
  blockTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1f78ff',
  },
  blockHeading: {
    fontSize: 16,
    fontWeight: '600',
    color: '#0d1b2a',
  },
  blockText: {
    fontSize: 14,
    color: '#1b263b',
  },
  blockMeta: {
    fontSize: 13,
    color: '#415a77',
  },
  blockStep: {
    fontSize: 13,
    color: '#1b263b',
  },
  errorText: {
    color: '#c1121f',
    textAlign: 'center',
    fontWeight: '600',
    marginBottom: 16,
  },
});
