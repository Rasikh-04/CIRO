import React, { useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Feather } from '@expo/vector-icons';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import HomeScreen from './screens/HomeScreen';
import AlertsScreen from './screens/AlertsScreen';
import SafeRoutesScreen from './screens/SafeRoutesScreen';
import ProfileScreen from './screens/ProfileScreen';
import CrisisDetailScreen from './screens/CrisisDetailScreen';
import SplashScreen from './screens/SplashScreen';
import { ThemeProvider, useTheme } from './theme/ThemeContext';

export type RootStackParamList = {
  Tabs: undefined;
  CrisisDetail: { crisisId: string };
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

function TabNavigator() {
  const { colors } = useTheme();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ color, size }) => {
          const icons: Record<string, keyof typeof Feather.glyphMap> = {
            Home: 'map',
            Alerts: 'alert-triangle',
            Routes: 'navigation',
            Profile: 'user',
          };
          return <Feather name={icons[route.name] ?? 'circle'} size={size} color={color} />;
        },
        tabBarActiveTintColor: colors.accentPrimary,
        tabBarInactiveTintColor: colors.textMuted,
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.bgSurface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'Map' }} />
      <Tab.Screen name="Alerts" component={AlertsScreen} />
      <Tab.Screen name="Routes" component={SafeRoutesScreen} options={{ title: 'Routes' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function AppNavigator() {
  const [splashDone, setSplashDone] = useState(false);

  if (!splashDone) {
    return <SplashScreen onReady={() => setSplashDone(true)} />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Tabs" component={TabNavigator} />
        <Stack.Screen name="CrisisDetail" component={CrisisDetailScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <SafeAreaProvider>
        <AppNavigator />
      </SafeAreaProvider>
    </ThemeProvider>
  );
}
