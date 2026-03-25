package com.example.mykilnbuddy_mobile;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.os.Handler;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.navigation.fragment.NavHostFragment;

import com.example.mykilnbuddy_mobile.databinding.FragmentFirstBinding;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;


public class FirstFragment extends Fragment {

    private FragmentFirstBinding binding;

    Handler handler = new Handler();
    Runnable runnable;

    private TextView textView_temperature;
    private TextView textView_timestamp;

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState
    ) {

        binding = FragmentFirstBinding.inflate(inflater, container, false);
        return binding.getRoot();

    }

    public void onViewCreated(@NonNull View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        binding.buttonFirst.setOnClickListener(v ->
                NavHostFragment.findNavController(FirstFragment.this)
                        .navigate(R.id.action_FirstFragment_to_SecondFragment)
        );


        // get textViews
        textView_temperature = view.findViewById(R.id.textView5);
        textView_timestamp = view.findViewById(R.id.textView6);

        // create runnable
        runnable = new Runnable() {
            @Override
            public void run() {
                makeApiRequest(1); // call API to get newest temperature values
                handler.postDelayed(this, 10000); // update data every 10 seconds
            }
        };

        // run runnable
        handler.post(runnable);
    }


    private String loadKey(Context context, String key) {
        SharedPreferences prefs = context.getSharedPreferences("my_prefs", Context.MODE_PRIVATE);
        return prefs.getString(key, "key required"); // "" is default
    }

    private void makeApiRequest(Integer history_length) {
        new Thread(() -> {
            try {

                InputStream is;
                String api_url;
                String anon_key;
                String x_api_key;

                try{
                    // api url TODO: remove after test
                    api_url = loadKey(requireContext(), "api_url");;

                    // anon key okay here, since it is publishable
                    anon_key = loadKey(requireContext(), "anon_key");

                    // x-api-key from internal storage
                    x_api_key = loadKey(requireContext(), "api_key");

                    URL url = new URL(api_url);
                    HttpURLConnection conn = (HttpURLConnection) url.openConnection();

                    conn.setRequestMethod("GET");
                    conn.setRequestProperty("Authorization", "Bearer " + anon_key);
                    conn.setRequestProperty("x-api-key", x_api_key);
                    conn.setRequestProperty("most-recent", history_length.toString());
                    conn.setConnectTimeout(5000); // connection timeout in ms


                    if (conn.getResponseCode() >= 400) {
                        is = conn.getErrorStream();
                    } else {
                        is = conn.getInputStream();
                    }
                } catch (Exception e) {
                    requireActivity().runOnUiThread(() -> {
                        textView_temperature.setText(String.valueOf(e.getMessage()));
                    });
                    throw new RuntimeException(e);
                }

                BufferedReader reader = new BufferedReader(new InputStreamReader(is));

                StringBuilder result = new StringBuilder();
                String line;

                while ((line = reader.readLine()) != null) {
                    result.append(line);
                }

                reader.close();

                JSONObject jObj = new JSONObject(result.toString());

                String temperature;
                String measured_at;
                String formatted;

                try {
                    JSONArray data = jObj.getJSONArray("data");
                    temperature = data.getJSONObject(0).getString("temperature");
                    measured_at = data.getJSONObject(0).getString("measured_at");

                    // parse iso timestamp
                    ZonedDateTime zdt = ZonedDateTime.parse(measured_at);

                    // change to format that is readable, like "25.03.2026 14:30"
                    DateTimeFormatter formatter = DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm:ss");
                    formatted = zdt.format(formatter);

                } catch (Exception e) {
                    requireActivity().runOnUiThread(() -> {
                        textView_temperature.setText(String.valueOf(e.getMessage()));
                    });
                    throw new RuntimeException(e);
                }

                requireActivity().runOnUiThread(() -> {
                    textView_temperature.setText(String.valueOf(temperature) + "°C");
                    textView_timestamp.setText(String.valueOf(formatted));
                });

            } catch (Exception e) {
                e.printStackTrace();
            }
        }).start();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

}