import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { Ionicons } from "@expo/vector-icons";
import { SafeAreaProvider } from "react-native-safe-area-context";
import HomeScreen from "./screens/HomeScreen";
import AlertsScreen from "./screens/AlertsScreen";
import SafeRoutesScreen from "./screens/SafeRoutesScreen";
import ProfileScreen from "./screens/ProfileScreen";

const Tab = createBottomTabNavigator();

export default function App() {
  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            tabBarIcon: ({ focused, color, size }) => {
              let iconName: keyof typeof Ionicons.glyphMap = "home";
              if (route.name === "Home") iconName = "home";
              else if (route.name === "Alerts") iconName = "alert-circle";
              else if (route.name === "Routes") iconName = "navigate";
              else if (route.name === "Profile") iconName = "person";
              return <Ionicons name={iconName} size={size} color={color} />;
            },
            tabBarActiveTintColor: "#2563EB",
            tabBarInactiveTintColor: "#94A3B8",
            headerShown: false,
            tabBarStyle: {
              backgroundColor: "#0F172A",
              borderTopColor: "#334155",
              borderTopWidth: 1,
            },
          })}
        >
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{ title: "Home" }}
          />
          <Tab.Screen
            name="Alerts"
            component={AlertsScreen}
            options={{ title: "Alerts" }}
          />
          <Tab.Screen
            name="Routes"
            component={SafeRoutesScreen}
            options={{ title: "Safe Routes" }}
          />
          <Tab.Screen
            name="Profile"
            component={ProfileScreen}
            options={{ title: "Profile" }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
