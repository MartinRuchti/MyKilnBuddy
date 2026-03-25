package com.example.mykilnbuddy_mobile;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;

import androidx.annotation.NonNull;
import androidx.fragment.app.Fragment;
import androidx.navigation.fragment.NavHostFragment;

import com.example.mykilnbuddy_mobile.databinding.FragmentSecondBinding;

import android.content.Context;
import android.content.SharedPreferences;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Toast;

import java.util.Objects;

public class SecondFragment extends Fragment {

    private FragmentSecondBinding binding;

    @Override
    public View onCreateView(
            @NonNull LayoutInflater inflater, ViewGroup container,
            Bundle savedInstanceState
    ) {

        binding = FragmentSecondBinding.inflate(inflater, container, false);
        return binding.getRoot();

    }

    public void onViewCreated(@NonNull View view, Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);

        binding.buttonSecond.setOnClickListener(v ->
                NavHostFragment.findNavController(SecondFragment.this)
                        .navigate(R.id.action_SecondFragment_to_FirstFragment)
        );

        // get text editors and button
        EditText editText_url = view.findViewById(R.id.editTextTextEmailAddress2);
        EditText editText_anon = view.findViewById(R.id.editTextTextPassword2);
        EditText editText_api = view.findViewById(R.id.editTextTextPassword);
        Button saveButton = view.findViewById(R.id.button);

        // set text to last saved key
        requireActivity().runOnUiThread(() -> {
            editText_url.setText(loadKey(requireContext(), "api_url"));
            editText_anon.setText(loadKey(requireContext(), "anon_key"));
            editText_api.setText(loadKey(requireContext(), "api_key"));
        });

        // create action to read and save api-key
        saveButton.setOnClickListener(v -> {
            // get api url
            String apiUrl = editText_url.getText().toString();
            saveKey(requireContext(), apiUrl, "api_url");

            // get anon key
            String anonKey = editText_anon.getText().toString();
            saveKey(requireContext(), anonKey, "anon_key");

            // get api key
            String apiKey = editText_api.getText().toString();
            saveKey(requireContext(), apiKey, "api_key");

            // prompt user
            Toast.makeText(getContext(), "Konfiguration gespeichert!", Toast.LENGTH_SHORT).show();
        });
    }

    // save api key
    public void saveKey(Context context, String apiKey, String name) {
        SharedPreferences prefs = context.getSharedPreferences("my_prefs", Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(name, apiKey);
        editor.apply();  // or commit(), apply() is asynchronous
    }

    private String loadKey(Context context, String key) {
        SharedPreferences prefs = context.getSharedPreferences("my_prefs", Context.MODE_PRIVATE);
        return prefs.getString(key, ""); // "" is default
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

}